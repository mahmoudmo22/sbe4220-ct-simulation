"""
Filtered Back Projection (FBP) Reconstruction — Phase 2 (Mahmoud Bahaa)
========================================================================

Implements the Filtered Back Projection algorithm for reconstructing 2D
CT images from sinogram data.  This is the standard analytical
reconstruction method used in clinical CT scanners.

Mathematical Foundation
-----------------------
FBP is derived from the **Fourier Slice Theorem**, which states:

    F₁D{ p(θ, s) }(ω) = F₂D{ μ(x, y) }(ω·cos θ, ω·sin θ)

In words: the 1D Fourier transform of a projection at angle θ gives
a radial line (slice) through the 2D Fourier transform of the object
at the same angle.

Direct inversion would require interpolating from a polar grid to a
Cartesian grid in 2D Fourier space.  FBP avoids this by combining
the inversion into two steps:

**Step 1 — Filtering** (in frequency domain):

    p_filtered(θ, s) = F⁻¹{ |ω| · H(ω) · F{ p(θ, s) } }

where |ω| is the ramp filter and H(ω) is an optional apodisation window.

**Step 2 — Back Projection** (in spatial domain):

    μ(x, y) = ∫₀^π  p_filtered(θ,  x·cos θ + y·sin θ)  dθ

For each pixel (x, y), the offset s = x·cos θ + y·sin θ determines
which detector bin to read from the filtered projection at angle θ.

Why the Ramp Filter |ω| Is Necessary
-------------------------------------
Without filtering, back projection produces a blurred reconstruction
because low frequencies are overrepresented in the radial Fourier
sampling.  In polar coordinates, the area element is ω·dω·dθ (not
dω·dθ), so points near the frequency origin are sampled more densely.
The |ω| filter compensates for this non-uniform density, effectively
performing a "Jacobian correction" from polar to Cartesian sampling.

The price is that |ω| amplifies high-frequency noise.  Apodisation
windows H(ω) are used to suppress the high-frequency noise at the cost
of some spatial resolution.

Filter Kernels Implemented
--------------------------
1. **Ram-Lak** (pure ramp):   H(ω) = 1
   → Maximum resolution, maximum noise amplification.

2. **Shepp-Logan**:           H(ω) = sinc(ω / 2ω_max)
   → Slight high-frequency roll-off; good balance.

3. **Cosine**:                H(ω) = cos(π ω / 2ω_max)
   → Moderate roll-off; smoother images.

4. **Hamming**:               H(ω) = 0.54 + 0.46·cos(π ω / ω_max)
   → Strong high-frequency suppression; smoothest images, lowest noise.
"""

import numpy as np


# ---------------------------------------------------------------------------
#  Filter Kernels
# ---------------------------------------------------------------------------

def make_filter(filter_name, n):
    """
    Create a frequency-domain filter for FBP reconstruction.

    The filter is constructed in the frequency domain and has length `n`.
    It consists of the ramp |ω| multiplied by an apodisation window H(ω).

    Parameters
    ----------
    filter_name : str
        One of ``'ram-lak'``, ``'shepp-logan'``, ``'cosine'``, ``'hamming'``.
    n : int
        Number of frequency bins (typically the next power of 2 above the
        number of detector bins, for efficient FFT).

    Returns
    -------
    filt : np.ndarray, shape (n,)
        The frequency-domain filter, suitable for element-wise multiplication
        with the FFT of a projection.

    Raises
    ------
    ValueError
        If `filter_name` is not one of the supported filters.

    Notes
    -----
    - Frequencies are normalised: ω_max = 0.5 (Nyquist).
    - The DC component (ω = 0) is set to a small positive value to avoid
      numerical issues, matching standard implementations.
    - The filter is real and symmetric, so it can be applied to each
      projection independently.
    """
    # Frequency axis (0 to n-1) / n  — the "digital frequency" in cycles/sample
    freqs = np.abs(np.fft.fftfreq(n))  # |ω|, normalised so Nyquist = 0.5

    # Start with the ramp filter |ω|
    filt = freqs.copy()

    # Apply the apodisation window
    omega_max = 0.5  # Nyquist frequency in normalised units

    filter_name_lower = filter_name.lower().replace("-", "").replace("_", "")

    if filter_name_lower == "ramlak":
        # Pure ramp — no additional windowing
        pass

    elif filter_name_lower == "shepplogan":
        # Shepp-Logan: sinc(ω / 2ω_max)
        # sinc(x) = sin(πx) / (πx);  np.sinc(x) = sin(πx) / (πx)
        window = np.sinc(freqs / (2 * omega_max))
        filt *= window

    elif filter_name_lower == "cosine":
        # Cosine window: cos(π ω / 2ω_max)
        window = np.cos(np.pi * freqs / (2 * omega_max))
        filt *= window

    elif filter_name_lower == "hamming":
        # Hamming window: 0.54 + 0.46 · cos(π ω / ω_max)
        window = 0.54 + 0.46 * np.cos(np.pi * freqs / omega_max)
        filt *= window

    else:
        raise ValueError(
            f"Unknown filter '{filter_name}'. "
            f"Choose from: 'ram-lak', 'shepp-logan', 'cosine', 'hamming'."
        )

    return filt


# ---------------------------------------------------------------------------
#  Filtered Back Projection
# ---------------------------------------------------------------------------

def filter_projections(sinogram, filter_name="ram-lak", detector_spacing=None):
    """
    Apply frequency-domain filtering to all projections in a sinogram.

    Each column (projection) of the sinogram is:
    1. Zero-padded to the next power of 2 for efficient FFT.
    2. Transformed to the frequency domain via FFT.
    3. Multiplied by the filter |ω| · H(ω).
    4. Inverse-FFT'd back to the spatial domain.

    Parameters
    ----------
    sinogram : np.ndarray, shape (num_detectors, num_angles)
        Input sinogram (projection data).
    filter_name : str, optional
        Filter kernel to use.  Default is ``'ram-lak'``.
    detector_spacing : float, optional
        Physical spacing between detector bins. If None, it assumes the 
        standard normalised geometry of width 2.0: 2.0 / (num_detectors - 1).

    Returns
    -------
    filtered_sinogram : np.ndarray, shape (num_detectors, num_angles)
        The filtered sinogram (same shape as input).

    Notes
    -----
    Filtering in the frequency domain implements the convolution:

        p_filtered(s) = p(s) * h(s)

    where h(s) is the impulse response of the filter.  The ramp filter
    h(s) has the analytical form:

        h(s) = 1/(4Δ²)     if s = 0
             = 0            if s is even
             = -1/(π²s²Δ²)  if s is odd

    where Δ is the detector spacing.  Computing this in the frequency
    domain via FFT is equivalent and more efficient.
    """
    num_detectors, num_angles = sinogram.shape

    if detector_spacing is None:
        # Avoid division by zero if num_detectors is 1 (unlikely)
        detector_spacing = 2.0 / max(1, num_detectors - 1)

    # Pad to next power of 2 for efficient FFT
    n_padded = int(2 ** np.ceil(np.log2(num_detectors)))

    # Build the filter
    filt = make_filter(filter_name, n_padded)
    
    # Scale filter by 1 / detector_spacing to match the continuous FT integration
    filt = filt / detector_spacing

    # Filter each projection
    filtered = np.zeros_like(sinogram)
    for j in range(num_angles):
        projection = sinogram[:, j]

        # FFT (zero-padded)
        proj_fft = np.fft.fft(projection, n=n_padded)

        # Apply filter (element-wise multiplication in frequency domain)
        proj_filtered_fft = proj_fft * filt

        # Inverse FFT and take the real part
        proj_filtered = np.real(np.fft.ifft(proj_filtered_fft))

        # Truncate back to original length
        filtered[:, j] = proj_filtered[:num_detectors]

    return filtered


def backproject(filtered_sinogram, angles_deg, output_size=None):
    """
    Perform the back-projection step of FBP.

    For each pixel (x, y) in the output image, and for each projection
    angle θ, compute the offset:

        s = x · cos θ + y · sin θ

    and interpolate the filtered projection value at that offset.  The
    pixel value is the sum over all angles:

        μ(x, y) = (π / N_angles) · Σ_θ  p_filtered(θ, s)

    Parameters
    ----------
    filtered_sinogram : np.ndarray, shape (num_detectors, num_angles)
        The filtered sinogram.
    angles_deg : np.ndarray, shape (num_angles,)
        Projection angles in degrees.
    output_size : int or None, optional
        Size of the output image (output_size × output_size).  If None,
        uses the number of detector bins.

    Returns
    -------
    reconstruction : np.ndarray, shape (output_size, output_size)
        The reconstructed image.

    Notes
    -----
    Linear interpolation is used when the computed offset s falls between
    detector bins.  Rays that fall outside the detector range contribute
    zero.
    """
    num_detectors, num_angles = filtered_sinogram.shape
    if output_size is None:
        output_size = num_detectors

    # Detector positions in normalised coordinates
    detector_positions = np.linspace(-1.0, 1.0, num_detectors)

    # Output image pixel coordinates
    coords = np.linspace(-1.0, 1.0, output_size)
    x_grid, y_grid = np.meshgrid(coords, coords)  # (N, N)

    reconstruction = np.zeros((output_size, output_size), dtype=np.float64)

    angles_rad = np.deg2rad(angles_deg)

    for j, angle in enumerate(angles_rad):
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)

        # Compute the offset s for every pixel
        s = x_grid * cos_a + y_grid * sin_a   # (N, N)

        # Interpolate the filtered projection at these offsets
        # Map s to detector index (floating point)
        det_idx = np.interp(
            s.ravel(),
            detector_positions,
            np.arange(num_detectors),
        ).reshape(output_size, output_size)

        # Linear interpolation between adjacent detector bins
        idx_lo = np.floor(det_idx).astype(int)
        idx_hi = idx_lo + 1
        frac = det_idx - idx_lo

        # Clip to valid range
        idx_lo_safe = np.clip(idx_lo, 0, num_detectors - 1)
        idx_hi_safe = np.clip(idx_hi, 0, num_detectors - 1)

        # Interpolated value
        proj_interp = (
            (1 - frac) * filtered_sinogram[idx_lo_safe, j]
            + frac * filtered_sinogram[idx_hi_safe, j]
        )

        # Mask pixels outside the detector range
        valid = (s >= detector_positions[0]) & (s <= detector_positions[-1])
        reconstruction += proj_interp * valid

    # Scale by dθ = π / N_angles  (the angular integration weight)
    d_theta = np.pi / num_angles
    reconstruction *= d_theta

    return reconstruction


def reconstruct_fbp(sinogram, angles_deg, filter_name="ram-lak",
                    output_size=None, detector_spacing=None):
    """
    Full FBP reconstruction: filter + back-project.

    This is the main entry point that combines filtering and back-projection
    into a single convenient function.

    Parameters
    ----------
    sinogram : np.ndarray, shape (num_detectors, num_angles)
        Input sinogram.
    angles_deg : np.ndarray, shape (num_angles,)
        Projection angles in degrees.
    filter_name : str, optional
        Filter kernel.  Default is ``'ram-lak'``.
    output_size : int or None, optional
        Size of the output image.
    detector_spacing : float, optional
        Physical spacing between detector bins. If None, uses default.

    Returns
    -------
    reconstruction : np.ndarray, shape (output_size, output_size)
        The reconstructed image.

    Example
    -------
    >>> from phantom import generate_shepp_logan
    >>> from forward_projection import generate_sinogram_fast
    >>> phantom = generate_shepp_logan(256)
    >>> sinogram, angles = generate_sinogram_fast(phantom, 180)
    >>> recon = reconstruct_fbp(sinogram, angles, filter_name='ram-lak')
    """
    filtered = filter_projections(sinogram, filter_name, detector_spacing=detector_spacing)
    reconstruction = backproject(filtered, angles_deg, output_size)
    return reconstruction


# ---------------------------------------------------------------------------
#  Utility: list available filters
# ---------------------------------------------------------------------------

AVAILABLE_FILTERS = ["ram-lak", "shepp-logan", "cosine", "hamming"]


def get_filter_descriptions():
    """
    Return a dictionary mapping filter names to human-readable descriptions.
    """
    return {
        "ram-lak": (
            "Ram-Lak (ramp): Pure |ω| filter. Maximum resolution, "
            "maximum noise amplification. H(ω) = 1."
        ),
        "shepp-logan": (
            "Shepp-Logan: Slight high-frequency roll-off via sinc window. "
            "H(ω) = sinc(ω / 2ω_max). Good balance of resolution and noise."
        ),
        "cosine": (
            "Cosine: Moderate high-frequency roll-off. "
            "H(ω) = cos(πω / 2ω_max). Smoother images than Shepp-Logan."
        ),
        "hamming": (
            "Hamming: Strong high-frequency suppression. "
            "H(ω) = 0.54 + 0.46·cos(πω / ω_max). Smoothest images, "
            "lowest noise, but reduced spatial resolution."
        ),
    }
