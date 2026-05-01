"""
Modulation Transfer Function (MTF) — Phase 4 (Rashed Mamdouh)
===============================================================

Implements MTF measurement using two methods: the Point Spread Function
(PSF) method and the Edge Spread Function (ESF) method.

Physics Background
------------------
The Modulation Transfer Function quantifies the CT system's ability to
preserve contrast at each spatial frequency.

    MTF(f) = 1   →  the system perfectly reproduces features at frequency f
    MTF(f) = 0   →  features at frequency f are completely lost

An ideal imaging system would have MTF(f) = 1 for all frequencies.  In
practice, MTF always decreases with increasing frequency due to finite
pixel size, finite detector aperture, reconstruction filter effects, and
finite angular sampling.

Mathematical Definition
-----------------------
The imaging system can be modelled as a linear shift-invariant (LSI)
system.  If the input is μ_true(x, y) and the output is μ_recon(x, y):

    μ_recon(x, y) = μ_true(x, y) ** PSF(x, y)

where ** denotes 2D convolution and PSF is the Point Spread Function
(the system's response to a point impulse δ(x, y)).

In the frequency domain, convolution becomes multiplication:

    M_recon(u, v) = M_true(u, v) · OTF(u, v)

where OTF (Optical Transfer Function) is the 2D Fourier transform of the
PSF.  The MTF is the magnitude of the OTF:

    MTF(u, v) = |OTF(u, v)| = |F{ PSF(x, y) }|

For a radially symmetric system (common assumption), the 2D MTF can be
reduced to a 1D function MTF(f) by radial averaging or by using a 1D
measurement method (edge/line).

Method 1: PSF Method
---------------------
1. Create a phantom with a single point (impulse) object.
2. Forward-project and reconstruct — the reconstruction IS the PSF.
3. Compute MTF = |FFT(PSF)|, normalised so MTF(0) = 1.

    Advantage: Directly gives the 2D PSF.
    Disadvantage: Low SNR because a single point has very little signal.

Method 2: Edge Method (more robust)
------------------------------------
1. Create a phantom with a sharp edge (step function).
2. Forward-project and reconstruct.
3. Extract a profile perpendicular to the edge → Edge Spread Function (ESF).
4. Differentiate ESF to get the Line Spread Function (LSF).
5. MTF = |FFT(LSF)|, normalised so MTF(0) = 1.

    Advantage: Much higher SNR because the edge extends over many pixels.
    Disadvantage: Gives a 1D MTF (along the direction perpendicular to the edge).

The relationship between PSF, LSF, and ESF:
    ESF(x) = ∫_{-∞}^{x} LSF(x') dx'
    LSF(x) = d/dx ESF(x)
    LSF(x) = ∫ PSF(x, y) dy        (line integral of PSF)
    MTF(f) = |F{LSF(x)}| / |F{LSF(x)}|_{f=0}
"""

import numpy as np


# ---------------------------------------------------------------------------
#  PSF-based MTF
# ---------------------------------------------------------------------------

def extract_psf(reconstruction, center, roi_size=32):
    """
    Extract the Point Spread Function (PSF) from a reconstruction of a
    point object.

    Parameters
    ----------
    reconstruction : np.ndarray, shape (N, N)
        Reconstructed image containing a point object.
    center : tuple of int
        (row, col) — the expected location of the point object.
    roi_size : int, optional
        Size of the square ROI to extract around the point.  Default is 32.

    Returns
    -------
    psf : np.ndarray, shape (roi_size, roi_size)
        The extracted PSF (centred on the point).
    """
    row, col = center
    half = roi_size // 2

    r_lo = max(row - half, 0)
    r_hi = min(row + half, reconstruction.shape[0])
    c_lo = max(col - half, 0)
    c_hi = min(col + half, reconstruction.shape[1])

    psf = reconstruction[r_lo:r_hi, c_lo:c_hi].copy()

    # Subtract baseline (minimum value) to isolate the point response
    psf -= psf.min()

    return psf


def compute_mtf_from_psf(psf):
    """
    Compute the 2D MTF from a Point Spread Function.

        MTF(u, v) = |FFT₂D{ PSF(x, y) }| / |FFT₂D{ PSF }|_{(0,0)}

    Parameters
    ----------
    psf : np.ndarray, shape (M, M)
        The 2D Point Spread Function.

    Returns
    -------
    mtf_2d : np.ndarray, shape (M, M)
        The 2D MTF (normalised to 1 at DC).
    freqs : np.ndarray, shape (M,)
        Spatial frequency axis (cycles per pixel).
    mtf_1d : np.ndarray
        Radially averaged 1D MTF.
    freq_1d : np.ndarray
        Corresponding spatial frequency axis for the 1D MTF.
    """
    # 2D FFT of the PSF
    psf_fft = np.fft.fft2(psf)
    mtf_2d = np.abs(np.fft.fftshift(psf_fft))

    # Normalise so that MTF(0,0) = 1
    dc = mtf_2d[mtf_2d.shape[0] // 2, mtf_2d.shape[1] // 2]
    if dc > 0:
        mtf_2d /= dc

    # Frequency axis
    M = psf.shape[0]
    freqs = np.fft.fftshift(np.fft.fftfreq(M))

    # Radially average to get 1D MTF
    freq_1d, mtf_1d = radial_average(mtf_2d)

    return mtf_2d, freqs, mtf_1d, freq_1d


def radial_average(image_2d):
    """
    Compute the radial average of a 2D array centred at the middle.

    Parameters
    ----------
    image_2d : np.ndarray, shape (M, M)
        2D array (assumed to be centred, e.g., fftshifted MTF).

    Returns
    -------
    radii : np.ndarray
        Frequency values (in pixel⁻¹ units).
    profile : np.ndarray
        Radially averaged values.
    """
    M = image_2d.shape[0]
    center = M // 2

    y, x = np.ogrid[:M, :M]
    r = np.sqrt((x - center) ** 2 + (y - center) ** 2).astype(int)

    max_r = min(center, M - center - 1)
    radii = np.arange(0, max_r + 1)
    profile = np.zeros(len(radii))
    counts = np.zeros(len(radii))

    for i in range(M):
        for j in range(M):
            dist = r[i, j]
            if dist <= max_r:
                profile[dist] += image_2d[i, j]
                counts[dist] += 1

    # Avoid division by zero
    valid = counts > 0
    profile[valid] /= counts[valid]

    # Convert radii to frequency (normalised, cycles per pixel)
    freq_radii = radii / M

    return freq_radii, profile


# ---------------------------------------------------------------------------
#  Edge-based MTF (ESF → LSF → MTF)
# ---------------------------------------------------------------------------

def extract_esf(reconstruction, edge_row_range, edge_col, direction="horizontal"):
    """
    Extract the Edge Spread Function (ESF) from a reconstruction.

    The ESF is a 1D profile taken perpendicular to a sharp edge in the
    reconstructed image.

    Parameters
    ----------
    reconstruction : np.ndarray, shape (N, N)
        Reconstructed image containing a sharp edge.
    edge_row_range : tuple of int
        (row_start, row_end) — rows over which to average the edge profile
        (for noise reduction).
    edge_col : int
        Approximate column position of the edge (used to centre extraction).
    direction : str, optional
        Direction of the edge profile.  ``"horizontal"`` means the profile
        is extracted along rows (perpendicular to a vertical edge).

    Returns
    -------
    esf : np.ndarray
        The edge spread function (1D profile across the edge).
    positions : np.ndarray
        Pixel positions along the profile.
    """
    row_start, row_end = edge_row_range

    # Average multiple rows for noise reduction
    edge_region = reconstruction[row_start:row_end, :]
    esf = np.mean(edge_region, axis=0)

    positions = np.arange(len(esf))

    return esf, positions


def esf_to_lsf(esf):
    """
    Differentiate the Edge Spread Function (ESF) to obtain the Line
    Spread Function (LSF).

        LSF(x) = d/dx ESF(x)

    Parameters
    ----------
    esf : np.ndarray
        1D edge spread function.

    Returns
    -------
    lsf : np.ndarray
        Line spread function (one element shorter than ESF unless padded).
    """
    lsf = np.diff(esf)

    # Smooth if needed (optional Gaussian smoothing could be added here)
    return lsf


def compute_mtf_from_edge(esf):
    """
    Compute the 1D MTF from an Edge Spread Function.

    Pipeline: ESF → differentiate → LSF → FFT → |·| → normalise → MTF

    Parameters
    ----------
    esf : np.ndarray
        1D edge spread function.

    Returns
    -------
    freq : np.ndarray
        Spatial frequency axis (cycles per pixel).
    mtf : np.ndarray
        1D MTF (normalised to 1 at f=0).

    Notes
    -----
    Only the positive frequencies are returned (up to Nyquist = 0.5
    cycles/pixel).
    """
    # Differentiate ESF to get LSF
    lsf = esf_to_lsf(esf)

    # FFT of LSF
    lsf_fft = np.fft.fft(lsf)
    mtf_full = np.abs(lsf_fft)

    # Normalise so MTF(0) = 1
    if mtf_full[0] > 0:
        mtf_full /= mtf_full[0]

    # Frequency axis
    n = len(lsf)
    freq_full = np.fft.fftfreq(n)

    # Keep only positive frequencies (up to Nyquist)
    positive = freq_full >= 0
    freq = freq_full[positive]
    mtf = mtf_full[positive]

    return freq, mtf


def compute_mtf_from_reconstruction(reconstruction, method="edge",
                                     point_center=None, roi_size=32,
                                     edge_row_range=None, edge_col=None):
    """
    Convenience function: compute MTF from a reconstructed image.

    Parameters
    ----------
    reconstruction : np.ndarray
        Reconstructed image.
    method : str
        ``"psf"`` or ``"edge"``.
    point_center : tuple of int or None
        For PSF method: (row, col) of the point insert.
    roi_size : int
        For PSF method: size of the PSF extraction ROI.
    edge_row_range : tuple of int or None
        For edge method: (row_start, row_end) rows to average.
    edge_col : int or None
        For edge method: approximate column of the edge.

    Returns
    -------
    freq : np.ndarray
        Spatial frequency axis.
    mtf : np.ndarray
        1D MTF curve.
    """
    if method.lower() == "psf":
        if point_center is None:
            raise ValueError("point_center required for PSF method")
        psf = extract_psf(reconstruction, point_center, roi_size)
        _, _, mtf, freq = compute_mtf_from_psf(psf)
        return freq, mtf

    elif method.lower() == "edge":
        if edge_row_range is None:
            # Default: middle 20% of the image (safely inside the edge insert bounds)
            N = reconstruction.shape[0]
            edge_row_range = (int(0.4 * N), int(0.6 * N))
        esf, _ = extract_esf(reconstruction, edge_row_range, edge_col)
        freq, mtf = compute_mtf_from_edge(esf)
        return freq, mtf

    else:
        raise ValueError(f"Unknown method '{method}'. Use 'psf' or 'edge'.")
