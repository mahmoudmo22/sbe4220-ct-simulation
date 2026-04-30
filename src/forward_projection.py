"""
Forward Projection Module — Phase 1 (Mahmoud Mohamed)
=====================================================

Implements the parallel-beam forward projector that simulates X-ray CT
data acquisition.  Given a 2D phantom image representing the linear
attenuation coefficient μ(x, y), this module computes sinograms — the
collection of projection data at multiple angles.

Physics Background
------------------
When an X-ray beam passes through an object, its intensity is attenuated
according to Beer-Lambert's law:

    I = I₀ · exp( − ∫ μ(x, y) dl )

where:
    I₀  = incident photon intensity
    I   = transmitted intensity at the detector
    μ   = linear attenuation coefficient [mm⁻¹]
    dl  = differential path length along the ray

The measured quantity (after taking the negative log) is the projection
value — a line integral of μ along the ray path:

    p = −ln(I / I₀) = ∫ μ(x, y) dl

Geometry
--------
We use **parallel-beam geometry**: at each projection angle θ, a set of
parallel rays traverse the object at evenly spaced offsets s from the
centre.  Each ray computes one line integral.

Mathematically, the Radon transform is:

    p(θ, s) = ∫∫ μ(x, y) · δ(x·cos θ + y·sin θ − s) dx dy

The 2D array p(θ, s) — projection values for all angles and detector
positions — is called the **sinogram** (because a point object traces a
sinusoidal curve in this space).
"""

import numpy as np


def _compute_line_integral(image, size, angle_rad, offset, coords):
    """
    Compute the line integral of μ along a single ray.

    Uses discrete ray-tracing: for each sample point along the ray, the
    attenuation value is interpolated from the image using nearest-neighbour
    sampling, and the contributions are summed.

    Parameters
    ----------
    image : np.ndarray, shape (size, size)
        The phantom image (attenuation coefficient map).
    size : int
        Image dimension (pixels per side).
    angle_rad : float
        Projection angle in radians.
    offset : float
        Perpendicular offset of the ray from the image centre (normalised
        coordinates, range approximately [-1, 1]).
    coords : np.ndarray
        1D array of sample positions along the ray direction (normalised).

    Returns
    -------
    line_integral : float
        The computed line integral ∫ μ dl for this ray.
    """
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)

    # Parametrise the ray.  The ray direction is (−sin θ, cos θ) and the
    # perpendicular is (cos θ, sin θ).  A ray at offset s is:
    #     x(t) = s · cos θ  −  t · sin θ
    #     y(t) = s · sin θ  +  t · cos θ
    x_samples = offset * cos_a - coords * sin_a
    y_samples = offset * sin_a + coords * cos_a

    # Convert normalised coordinates to pixel indices
    col_idx = ((x_samples + 1) / 2 * (size - 1)).astype(int)
    row_idx = ((y_samples + 1) / 2 * (size - 1)).astype(int)

    # Clip to image bounds
    valid = (col_idx >= 0) & (col_idx < size) & (row_idx >= 0) & (row_idx < size)
    col_idx = col_idx[valid]
    row_idx = row_idx[valid]

    # The pixel spacing in normalised coordinates
    pixel_spacing = 2.0 / (size - 1)

    # Sum of μ values × step size = discrete approximation of the line integral
    line_integral = np.sum(image[row_idx, col_idx]) * pixel_spacing

    return line_integral


def generate_sinogram(image, num_angles, angle_range=(0, 180)):
    """
    Generate a sinogram from a 2D phantom image using parallel-beam projection.

    For each projection angle θ, parallel rays are cast across the image at
    evenly spaced detector positions.  Each ray computes the line integral
    of the attenuation coefficient along its path.

    Parameters
    ----------
    image : np.ndarray, shape (N, N)
        The phantom image (2D attenuation map).  Must be square.
    num_angles : int
        Number of projection angles to compute (evenly spaced over
        `angle_range`).
    angle_range : tuple of float, optional
        (start_deg, end_deg).  Default is (0, 180), which is sufficient
        for parallel-beam geometry due to symmetry (projections at θ and
        θ + 180° contain the same information for parallel beams).

    Returns
    -------
    sinogram : np.ndarray, shape (num_detectors, num_angles)
        The sinogram.  Rows correspond to detector positions (offsets),
        columns correspond to projection angles.
    angles : np.ndarray, shape (num_angles,)
        The projection angles in degrees.

    Notes
    -----
    - The number of detector bins is set equal to the image size N to
      maintain consistent sampling.
    - Rays that fall entirely outside the image contribute zero.
    - This implementation uses nearest-neighbour interpolation for
      simplicity.  For higher accuracy, bilinear interpolation can be
      used (at the cost of performance).

    Example
    -------
    >>> from phantom import generate_shepp_logan
    >>> phantom = generate_shepp_logan(256)
    >>> sinogram, angles = generate_sinogram(phantom, num_angles=180)
    >>> sinogram.shape
    (256, 180)
    """
    size = image.shape[0]
    assert image.shape[0] == image.shape[1], "Image must be square."

    # Projection angles
    angles_deg = np.linspace(angle_range[0], angle_range[1],
                             num_angles, endpoint=False)
    angles_rad = np.deg2rad(angles_deg)

    # Detector offsets — evenly spaced across the image diagonal
    # The maximum offset for a unit circle inscribed in [-1, 1] is √2
    # but we use 1.0 to match the phantom extent nicely
    num_detectors = size
    offsets = np.linspace(-1.0, 1.0, num_detectors)

    # Sample positions along each ray (parameterised by t)
    num_samples = int(np.ceil(size * np.sqrt(2)))
    ray_samples = np.linspace(-1.0, 1.0, num_samples)

    # Allocate sinogram:  shape = (num_detectors, num_angles)
    sinogram = np.zeros((num_detectors, num_angles), dtype=np.float64)

    for j, angle in enumerate(angles_rad):
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)

        for i, offset in enumerate(offsets):
            sinogram[i, j] = _compute_line_integral(
                image, size, angle, offset, ray_samples
            )

    return sinogram, angles_deg


def generate_sinogram_fast(image, num_angles, angle_range=(0, 180)):
    """
    Fast (vectorised) sinogram generation using parallel-beam projection.

    This is a fully vectorised implementation that processes all detector
    positions simultaneously for each projection angle, offering
    significant speedup over ``generate_sinogram``.

    Parameters
    ----------
    image : np.ndarray, shape (N, N)
        The phantom image (2D attenuation map).  Must be square.
    num_angles : int
        Number of projection angles.
    angle_range : tuple of float, optional
        (start_deg, end_deg).  Default is (0, 180).

    Returns
    -------
    sinogram : np.ndarray, shape (num_detectors, num_angles)
    angles : np.ndarray, shape (num_angles,)

    Notes
    -----
    This function is mathematically identical to ``generate_sinogram`` but
    uses broadcasting and vectorised NumPy operations for speed. It is the
    recommended version for normal use.
    """
    size = image.shape[0]
    assert image.shape[0] == image.shape[1], "Image must be square."

    angles_deg = np.linspace(angle_range[0], angle_range[1],
                             num_angles, endpoint=False)
    angles_rad = np.deg2rad(angles_deg)

    num_detectors = size
    offsets = np.linspace(-1.0, 1.0, num_detectors)

    num_samples = int(np.ceil(size * np.sqrt(2)))
    t_samples = np.linspace(-1.0, 1.0, num_samples)
    pixel_spacing = 2.0 / (size - 1)

    sinogram = np.zeros((num_detectors, num_angles), dtype=np.float64)

    for j, angle in enumerate(angles_rad):
        cos_a = np.cos(angle)
        sin_a = np.sin(angle)

        # Vectorise over all offsets and all sample points simultaneously
        # offsets: (num_detectors,),  t_samples: (num_samples,)
        # Use broadcasting: (num_detectors, 1) and (1, num_samples)
        s = offsets[:, np.newaxis]       # (D, 1)
        t = t_samples[np.newaxis, :]     # (1, S)

        x = s * cos_a - t * sin_a       # (D, S)
        y = s * sin_a + t * cos_a       # (D, S)

        # Convert to pixel indices
        col = ((x + 1) / 2 * (size - 1)).astype(int)
        row = ((y + 1) / 2 * (size - 1)).astype(int)

        # Mask valid indices
        valid = (col >= 0) & (col < size) & (row >= 0) & (row < size)

        # Clamp for safe indexing (masked values will be zeroed out)
        col_safe = np.clip(col, 0, size - 1)
        row_safe = np.clip(row, 0, size - 1)

        # Sample the image and zero-out invalid samples
        samples = image[row_safe, col_safe] * valid

        # Sum along the ray direction (axis=1) and scale by pixel spacing
        sinogram[:, j] = np.sum(samples, axis=1) * pixel_spacing

    return sinogram, angles_deg


def sinogram_to_intensity(sinogram, I0):
    """
    Convert a sinogram (line integrals) to detected photon intensities.

    Applies Beer-Lambert's law in the "forward" direction:
        I = I₀ · exp(−p)

    where p is the projection value (line integral of μ).

    Parameters
    ----------
    sinogram : np.ndarray
        Sinogram of projection values (line integrals).
    I0 : float
        Incident photon count (controls dose level).

    Returns
    -------
    intensity : np.ndarray
        Detected photon intensities (same shape as sinogram).
    """
    return I0 * np.exp(-sinogram)


def intensity_to_sinogram(intensity, I0):
    """
    Convert detected photon intensities back to sinogram values (line
    integrals) by applying the log transform.

        p = −ln(I / I₀)

    Parameters
    ----------
    intensity : np.ndarray
        Detected photon intensities.
    I0 : float
        Incident photon count.

    Returns
    -------
    sinogram : np.ndarray
        Sinogram of projection values.

    Notes
    -----
    Intensity values of zero are clipped to a small positive number to
    avoid log(0) = −∞.
    """
    intensity_safe = np.clip(intensity, 1e-10, None)
    return -np.log(intensity_safe / I0)
