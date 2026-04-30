"""
Noise Modeling & Dose Simulation — Phase 3 (Mohamed Ashraf)
============================================================

Implements realistic noise modeling for the CT simulation pipeline.
Noise is added in the **pre-log intensity domain** (before the
logarithmic transform) because photon detection follows Poisson
statistics.

Physics Background
------------------
In a real CT scanner, X-ray photons are counted by detectors.  Photon
counting is inherently a **Poisson process**: if the expected number of
detected photons is N, the actual measured count follows Poisson(N),
meaning:

    Variance(N_measured) = E[N_measured] = N

This gives a relative noise (coefficient of variation) of:

    σ/μ = 1/√N

The key insight is that noise is multiplicative (or signal-dependent) in
the intensity domain — regions that receive fewer photons (e.g., behind
dense bone) are noisier.

The Noise Pipeline
------------------
1. Start with the clean sinogram p = ∫μ dl  (line integrals).
2. Convert to intensity: I_clean = I₀ · exp(−p).
3. Apply Poisson noise: I_noisy ~ Poisson(I_clean).
4. Log-transform back: p_noisy = −ln(I_noisy / I₀).

Why add noise in the intensity domain? Because Poisson statistics apply
to **photon counts**, not to line integrals (which are derived
quantities).  The log transform then propagates the noise into the
sinogram domain, where the noise variance is approximately:

    Var(p_noisy) ≈ 1 / I_clean = exp(p) / I₀

This means:
- Higher dose (larger I₀) → less noise in the sinogram.
- Thicker/denser objects (larger p) → more noise (because fewer
  photons reach the detector through these paths).

Dose-Noise Relationship
------------------------
Since σ_sinogram ∝ 1/√I₀ and I₀ is proportional to the radiation dose:

    σ ∝ 1/√(dose)

Halving the dose increases noise by a factor of √2 ≈ 1.41.  This is the
fundamental physics behind the **dose-quality trade-off** in CT, and the
motivation for the ALARA principle ("As Low As Reasonably Achievable") —
use the minimum dose that still provides diagnostically acceptable image
quality.
"""

import numpy as np


def add_poisson_noise(sinogram, I0, rng=None):
    """
    Apply Poisson noise to a sinogram via the pre-log intensity domain.

    This is the physically correct way to add noise to CT projection data:
    1. Convert projection values (line integrals) to expected photon counts.
    2. Draw Poisson-distributed random samples (simulating photon counting).
    3. Convert back to the projection domain via the log transform.

    Parameters
    ----------
    sinogram : np.ndarray
        Clean sinogram (line integral values p = ∫μ dl).  All values
        should be ≥ 0.
    I0 : float
        Incident photon count per detector bin per projection.  Controls
        the dose level:
        - I₀ = 10⁶ : high dose (clinical quality)
        - I₀ = 10⁵ : moderate dose
        - I₀ = 10⁴ : low dose
        - I₀ = 10³ : very low dose (very noisy)
    rng : np.random.Generator or int or None, optional
        Random number generator or seed.  If None, uses default RNG.

    Returns
    -------
    noisy_sinogram : np.ndarray
        Sinogram with Poisson noise added (same shape as input).
    noisy_intensity : np.ndarray
        The noisy photon counts (before log transform), useful for analysis.

    Notes
    -----
    - Intensity values of zero (total attenuation — no photons detected)
      are clipped to 1 to avoid log(0).  This is the "photon starvation"
      regime and produces maximum noise in those bins.
    - The noise is **signal-dependent**: rays that pass through more
      attenuating material have fewer photons and thus higher relative noise.

    Example
    -------
    >>> from phantom import generate_shepp_logan
    >>> from forward_projection import generate_sinogram_fast
    >>> phantom = generate_shepp_logan(256)
    >>> sino, angles = generate_sinogram_fast(phantom, 180)
    >>> noisy_sino, _ = add_poisson_noise(sino, I0=1e5)
    """
    if rng is None:
        rng = np.random.default_rng()
    elif isinstance(rng, (int, np.integer)):
        rng = np.random.default_rng(rng)

    # Step 1: Convert to expected intensity (photon count)
    #   I_expected = I₀ · exp(−p)
    expected_intensity = I0 * np.exp(-sinogram)

    # Step 2: Draw Poisson samples
    #   I_measured ~ Poisson(I_expected)
    # Note: np.random.Generator.poisson requires non-negative integers,
    # but accepts floats (rounded internally).  Very large values may need
    # special handling.
    noisy_intensity = rng.poisson(lam=expected_intensity).astype(np.float64)

    # Step 3: Convert back to sinogram domain
    #   p_noisy = −ln(I_measured / I₀)
    # Clip to avoid log(0)
    noisy_intensity_safe = np.clip(noisy_intensity, 1.0, None)
    noisy_sinogram = -np.log(noisy_intensity_safe / I0)

    return noisy_sinogram, noisy_intensity


def add_gaussian_noise(sinogram, sigma, rng=None):
    """
    Add Gaussian (white) noise directly to the sinogram.

    This is a simplified noise model that can be useful for quick tests or
    comparisons, but is **not physically accurate** for CT.  In real CT,
    noise is Poisson in the intensity domain, not Gaussian in the
    projection domain.

    Parameters
    ----------
    sinogram : np.ndarray
        Clean sinogram.
    sigma : float
        Standard deviation of the additive Gaussian noise.
    rng : np.random.Generator or int or None, optional
        Random number generator or seed.

    Returns
    -------
    noisy_sinogram : np.ndarray
        Sinogram with Gaussian noise added.
    """
    if rng is None:
        rng = np.random.default_rng()
    elif isinstance(rng, (int, np.integer)):
        rng = np.random.default_rng(rng)

    noise = rng.normal(0, sigma, size=sinogram.shape)
    return sinogram + noise


def generate_dose_series(sinogram, dose_levels=None, rng=None):
    """
    Generate noisy sinograms at multiple dose levels.

    Useful for dose-vs-quality experiments: at each dose level, Poisson
    noise is applied with a different I₀, and the resulting noisy sinogram
    is returned.

    Parameters
    ----------
    sinogram : np.ndarray
        Clean sinogram.
    dose_levels : list of float or None, optional
        List of I₀ values to simulate.  Default is
        ``[1e6, 1e5, 1e4, 1e3]``.
    rng : np.random.Generator or int or None, optional
        Random number generator or seed.  Using a fixed seed ensures
        reproducibility across experiments.

    Returns
    -------
    results : dict
        Dictionary mapping each dose level to a dict with keys:
        - ``"noisy_sinogram"`` : np.ndarray
        - ``"noisy_intensity"`` : np.ndarray
        - ``"I0"`` : float

    Example
    -------
    >>> results = generate_dose_series(clean_sinogram, dose_levels=[1e5, 1e4])
    >>> noisy_1e5 = results[1e5]["noisy_sinogram"]
    """
    if dose_levels is None:
        dose_levels = [1e6, 1e5, 1e4, 1e3]

    if rng is None:
        rng = np.random.default_rng(42)
    elif isinstance(rng, (int, np.integer)):
        rng = np.random.default_rng(rng)

    results = {}
    for I0 in dose_levels:
        noisy_sino, noisy_int = add_poisson_noise(sinogram, I0, rng=rng)
        results[I0] = {
            "noisy_sinogram": noisy_sino,
            "noisy_intensity": noisy_int,
            "I0": I0,
        }

    return results


def compute_noise_statistics(clean_sinogram, noisy_sinogram,
                             clean_intensity=None, noisy_intensity=None,
                             I0=None):
    """
    Compute noise statistics to verify noise model correctness.

    Compares measured noise properties against theoretical predictions
    based on Poisson statistics.

    Parameters
    ----------
    clean_sinogram : np.ndarray
        Noise-free sinogram.
    noisy_sinogram : np.ndarray
        Noisy sinogram (same shape as clean).
    clean_intensity : np.ndarray or None
        Expected intensity I₀·exp(−p).  If None and I0 is given, computed
        internally.
    noisy_intensity : np.ndarray or None
        Measured (noisy) intensity.
    I0 : float or None
        Incident photon count.

    Returns
    -------
    stats : dict
        Dictionary with:
        - ``"sino_noise_mean"`` : mean of (noisy − clean) in sinogram domain
        - ``"sino_noise_std"`` : std of noise in sinogram domain
        - ``"sino_noise_std_theoretical"`` : theoretical std ≈ 1/√⟨I⟩
          (if I0 is provided)
        - ``"intensity_noise_mean"`` : mean of intensity noise (should ≈ 0)
        - ``"intensity_noise_var"`` : variance of intensity noise
        - ``"intensity_mean"`` : mean of expected intensity (= theoretical
          Poisson variance)
    """
    noise = noisy_sinogram - clean_sinogram

    stats = {
        "sino_noise_mean": np.mean(noise),
        "sino_noise_std": np.std(noise),
    }

    if I0 is not None:
        if clean_intensity is None:
            clean_intensity = I0 * np.exp(-clean_sinogram)
        # Theoretical sinogram noise std ≈ 1 / √(I_expected)  (average)
        theoretical_std = np.mean(1.0 / np.sqrt(np.clip(clean_intensity, 1, None)))
        stats["sino_noise_std_theoretical"] = theoretical_std

    if noisy_intensity is not None and clean_intensity is not None:
        int_noise = noisy_intensity - clean_intensity
        stats["intensity_noise_mean"] = np.mean(int_noise)
        stats["intensity_noise_var"] = np.var(int_noise)
        stats["intensity_mean"] = np.mean(clean_intensity)
        # For Poisson: variance should ≈ mean
        stats["poisson_variance_ratio"] = (
            np.var(int_noise) / np.mean(clean_intensity)
        )

    return stats


def estimate_snr_vs_dose(sinogram, dose_levels=None, rng=None):
    """
    Compute SNR in the sinogram domain for multiple dose levels.

    SNR is defined as the mean signal divided by the noise standard
    deviation.  For Poisson noise, we expect SNR ∝ √I₀.

    Parameters
    ----------
    sinogram : np.ndarray
        Clean sinogram.
    dose_levels : list of float or None
        Dose levels to evaluate.
    rng : np.random.Generator or int or None
        Random number generator or seed.

    Returns
    -------
    snr_values : dict
        Mapping dose level → SNR value.
    """
    if dose_levels is None:
        dose_levels = [1e6, 1e5, 1e4, 1e3]
    if rng is None:
        rng = np.random.default_rng(42)
    elif isinstance(rng, (int, np.integer)):
        rng = np.random.default_rng(rng)

    snr_values = {}
    for I0 in dose_levels:
        noisy_sino, _ = add_poisson_noise(sinogram, I0, rng=rng)
        noise = noisy_sino - sinogram
        snr = np.mean(sinogram) / np.std(noise)
        snr_values[I0] = snr

    return snr_values
