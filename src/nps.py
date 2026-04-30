"""
Noise Power Spectrum (NPS) — Phase 4 (Rashed Mamdouh)
======================================================

Implements NPS computation for characterising noise texture in
reconstructed CT images.

Physics Background
------------------
Standard deviation σ gives a single number for the total noise power.
However, two images can have the same σ but very different noise
*textures* — one may be fine-grained (high-frequency noise) while
another is blobby (low-frequency noise).

The Noise Power Spectrum decomposes the noise into its frequency
components, revealing **where** in the frequency domain the noise
energy sits.  This is critical for understanding image quality because:

1. The reconstruction filter directly shapes the NPS.
   - Ram-Lak: amplifies high frequencies → NPS peaks at high f.
   - Hamming: suppresses high frequencies → NPS rolls off at high f.

2. Noise at different frequencies has different perceptual and
   diagnostic impact.  High-frequency noise appears as fine graininess;
   low-frequency noise appears as blotchy patterns that can mimic
   pathology.

Mathematical Definition
-----------------------
For a uniform region of the reconstructed image containing only noise
(after subtracting the mean):

    NPS(u, v) = (Δx · Δy) / (Nx · Ny) · ⟨|F{ ROI(x,y) − mean(ROI) }|²⟩

where:
    Δx, Δy  = pixel spacings
    Nx, Ny  = ROI dimensions (in pixels)
    F{·}    = 2D Fourier transform
    ⟨·⟩     = ensemble average over multiple ROIs

The radially averaged 1D NPS is obtained by averaging the 2D NPS over
annular rings of constant frequency:

    NPS(f) = (1/N_ring) · Σ_{|(u,v)|∈[f, f+Δf]} NPS(u, v)

Key Property
------------
The integral of NPS over all frequencies equals the total noise variance:

    σ² = ∫∫ NPS(u, v) du dv

This connects the single-number metric (σ) to the frequency-resolved
characterisation (NPS).
"""

import numpy as np


def extract_uniform_rois(image, roi_size=64, num_rois=16, center=None,
                         search_radius=None, rng=None):
    """
    Extract multiple square ROIs from a uniform region of the image.

    The ROIs are used to estimate the NPS.  They should come from a
    region with approximately constant mean value (i.e., a uniform
    background) so that the only variation within each ROI is noise.

    Parameters
    ----------
    image : np.ndarray, shape (N, N)
        Reconstructed image.
    roi_size : int, optional
        Side length of each square ROI.  Default is 64.
    num_rois : int, optional
        Number of ROIs to extract.  More ROIs give a smoother NPS
        estimate.  Default is 16.
    center : tuple of int or None, optional
        (row, col) centre of the uniform region.  If None, uses the
        image centre.
    search_radius : int or None, optional
        Maximum displacement from `center` for placing ROI centres.  If
        None, set to ``image.shape[0] // 6``.
    rng : np.random.Generator or int or None, optional
        Random number generator or seed for reproducible ROI placement.

    Returns
    -------
    rois : list of np.ndarray
        List of extracted ROIs, each of shape (roi_size, roi_size).
    roi_positions : list of tuple
        (row, col) top-left corner of each extracted ROI.
    """
    if rng is None:
        rng = np.random.default_rng(42)
    elif isinstance(rng, (int, np.integer)):
        rng = np.random.default_rng(rng)

    N = image.shape[0]
    if center is None:
        center = (N // 2, N // 2)
    if search_radius is None:
        search_radius = N // 6

    half_roi = roi_size // 2
    rois = []
    positions = []

    attempts = 0
    max_attempts = num_rois * 20

    while len(rois) < num_rois and attempts < max_attempts:
        attempts += 1

        # Random centre within the search region
        r_offset = rng.integers(-search_radius, search_radius + 1)
        c_offset = rng.integers(-search_radius, search_radius + 1)
        r_center = center[0] + r_offset
        c_center = center[1] + c_offset

        # Check bounds
        r_lo = r_center - half_roi
        c_lo = c_center - half_roi
        r_hi = r_lo + roi_size
        c_hi = c_lo + roi_size

        if r_lo < 0 or c_lo < 0 or r_hi > N or c_hi > N:
            continue

        roi = image[r_lo:r_hi, c_lo:c_hi].copy()
        rois.append(roi)
        positions.append((r_lo, c_lo))

    return rois, positions


def compute_nps_2d(rois, pixel_size=1.0):
    """
    Compute the 2D Noise Power Spectrum from a set of ROIs.

    For each ROI:
    1. Subtract the mean (isolate the noise).
    2. Compute |FFT₂D{noise}|².
    3. Average over all ROIs.
    4. Scale by pixel dimensions.

    Parameters
    ----------
    rois : list of np.ndarray
        List of square ROIs from a uniform region.
    pixel_size : float, optional
        Physical pixel size (e.g., in mm).  Default is 1.0 (dimensionless).

    Returns
    -------
    nps_2d : np.ndarray
        The 2D NPS (fftshifted so DC is at centre).
    freq_x : np.ndarray
        Spatial frequency axis for x-direction.
    freq_y : np.ndarray
        Spatial frequency axis for y-direction.
    """
    roi_size = rois[0].shape[0]
    num_rois = len(rois)

    nps_sum = np.zeros((roi_size, roi_size), dtype=np.float64)

    for roi in rois:
        # Subtract mean to isolate noise
        noise = roi - np.mean(roi)

        # 2D FFT and power spectrum
        noise_fft = np.fft.fft2(noise)
        power = np.abs(noise_fft) ** 2

        nps_sum += power

    # Average over ROIs and scale
    # NPS = (Δx · Δy) / (Nx · Ny) · ⟨|FFT{noise}|²⟩
    nps_2d = (pixel_size ** 2 / roi_size ** 2) * (nps_sum / num_rois)

    # Shift DC to centre
    nps_2d = np.fft.fftshift(nps_2d)

    # Frequency axes
    freq = np.fft.fftshift(np.fft.fftfreq(roi_size, d=pixel_size))
    freq_x = freq
    freq_y = freq

    return nps_2d, freq_x, freq_y


def radial_average_nps(nps_2d, freq_x):
    """
    Compute the radially averaged 1D NPS from the 2D NPS.

    The 2D NPS is assumed to be roughly radially symmetric (true for
    most CT reconstruction methods).  Radial averaging reduces noise in
    the NPS estimate and produces a 1D curve NPS(f) that is easier to
    interpret and compare.

    Parameters
    ----------
    nps_2d : np.ndarray, shape (M, M)
        2D NPS (fftshifted, DC at centre).
    freq_x : np.ndarray, shape (M,)
        Spatial frequency axis.

    Returns
    -------
    freq_1d : np.ndarray
        Radial frequency axis.
    nps_1d : np.ndarray
        Radially averaged 1D NPS.
    """
    M = nps_2d.shape[0]
    center = M // 2

    # Compute distance from centre for each pixel
    y, x = np.ogrid[:M, :M]
    r = np.sqrt((x - center) ** 2 + (y - center) ** 2).astype(int)

    # Maximum radius
    max_r = min(center, M - center - 1)

    # Bin NPS values by radius
    nps_1d = np.zeros(max_r + 1)
    counts = np.zeros(max_r + 1)

    for i in range(M):
        for j in range(M):
            dist = r[i, j]
            if dist <= max_r:
                nps_1d[dist] += nps_2d[i, j]
                counts[dist] += 1

    valid = counts > 0
    nps_1d[valid] /= counts[valid]

    # Frequency axis (use frequency spacing from freq_x)
    df = np.abs(freq_x[1] - freq_x[0]) if len(freq_x) > 1 else 1.0
    freq_1d = np.arange(max_r + 1) * df

    return freq_1d, nps_1d


def compute_nps(image, roi_size=64, num_rois=16, center=None,
                pixel_size=1.0, rng=None):
    """
    Full NPS computation pipeline: extract ROIs → 2D NPS → radial average.

    This is the main convenience function for NPS measurement.

    Parameters
    ----------
    image : np.ndarray, shape (N, N)
        Reconstructed image (should contain a uniform region with noise).
    roi_size : int, optional
        Side length of each square ROI.
    num_rois : int, optional
        Number of ROIs to extract.
    center : tuple of int or None, optional
        Centre of the uniform region.
    pixel_size : float, optional
        Physical pixel size.
    rng : np.random.Generator or int or None, optional
        Random number generator or seed.

    Returns
    -------
    freq_1d : np.ndarray
        Radial frequency axis.
    nps_1d : np.ndarray
        Radially averaged 1D NPS.
    nps_2d : np.ndarray
        Full 2D NPS.
    freq_2d : np.ndarray
        2D frequency axis.

    Example
    -------
    >>> freq, nps, _, _ = compute_nps(noisy_reconstruction,
    ...                                roi_size=64, num_rois=32)
    """
    rois, _ = extract_uniform_rois(
        image, roi_size=roi_size, num_rois=num_rois,
        center=center, rng=rng
    )

    nps_2d, freq_x, freq_y = compute_nps_2d(rois, pixel_size=pixel_size)
    freq_1d, nps_1d = radial_average_nps(nps_2d, freq_x)

    return freq_1d, nps_1d, nps_2d, freq_x


def verify_nps_integral(nps_1d, freq_1d, measured_variance):
    """
    Verify the NPS by checking that its integral approximates σ².

    The integral of NPS over all frequencies should equal the total
    noise variance:

        σ² ≈ ∫ NPS(f) · 2πf df    (in polar, with radial averaging)

    For a discrete approximation, we simply check:

        σ² ≈ Σ NPS(f) · Δf

    (this is approximate due to radial binning).

    Parameters
    ----------
    nps_1d : np.ndarray
        Radially averaged 1D NPS.
    freq_1d : np.ndarray
        Frequency axis.
    measured_variance : float
        Directly measured noise variance from the image.

    Returns
    -------
    info : dict
        - ``"nps_integral"`` : the integrated NPS.
        - ``"measured_variance"`` : the directly measured σ².
        - ``"ratio"`` : nps_integral / measured_variance (should be ≈ 1).
    """
    df = freq_1d[1] - freq_1d[0] if len(freq_1d) > 1 else 1.0
    nps_integral = np.sum(nps_1d) * df

    return {
        "nps_integral": nps_integral,
        "measured_variance": measured_variance,
        "ratio": nps_integral / measured_variance if measured_variance > 0 else np.inf,
    }
