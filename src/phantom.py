"""
Phantom Generation Module — Phase 1 (Mahmoud Mohamed)
=====================================================

Implements two phantom types for the CT simulation:

1. **Shepp-Logan Phantom**: The standard analytical phantom composed of 10
   parameterized ellipses with known attenuation coefficients. Used for
   visual reconstruction quality assessment.

2. **QA (Quality Assurance) Phantom**: A custom-designed phantom with
   embedded geometric features for quantitative metrics evaluation:
   - High-contrast point insert → for PSF / MTF measurement
   - Sharp edge insert → for ESF-based MTF measurement
   - Low-contrast inserts at known μ values → for CNR measurement
   - Uniform background region → for NPS measurement

Physics Background:
    Each pixel in the phantom represents the linear attenuation coefficient
    μ(x, y) at that position.  In a real CT system, μ depends on the tissue
    type and the X-ray photon energy.  Typical values at diagnostic energies
    (~70 keV): water ≈ 0.019 mm⁻¹, bone ≈ 0.048 mm⁻¹, air ≈ 0.
    The Shepp-Logan phantom uses normalised values (0–2) for convenience.
"""

import numpy as np


# ---------------------------------------------------------------------------
#  Shepp-Logan Phantom
# ---------------------------------------------------------------------------

# Standard Shepp-Logan ellipse parameters (modified contrast version)
# Each row: (value, a, b, x0, y0, theta_deg)
#   value   — additive attenuation coefficient contribution
#   a, b    — semi-axes of the ellipse (fraction of image radius)
#   x0, y0  — centre position (fraction of image radius)
#   theta   — rotation angle in degrees (counter-clockwise)
SHEPP_LOGAN_PARAMS = np.array([
    [ 2.00, 0.6900, 0.9200,  0.0000,  0.0000,   0],   # outer skull
    [-0.98, 0.6624, 0.8740,  0.0000, -0.0184,   0],   # brain interior
    [-0.02, 0.1100, 0.3100,  0.2200,  0.0000, -18],   # right ventricle
    [-0.02, 0.1600, 0.4100, -0.2200,  0.0000,  18],   # left ventricle
    [ 0.01, 0.2100, 0.2500,  0.0000,  0.3500,   0],   # top tumour
    [ 0.01, 0.0460, 0.0460,  0.0000,  0.1000,   0],   # small tumour
    [ 0.01, 0.0460, 0.0460,  0.0000, -0.1000,   0],   # small tumour
    [ 0.01, 0.0460, 0.0230, -0.0800, -0.6050,   0],   # bottom feature
    [ 0.01, 0.0230, 0.0230,  0.0000, -0.6060,   0],   # bottom feature
    [ 0.01, 0.0230, 0.0460,  0.0600, -0.6050,   0],   # bottom feature
])


def _ellipse_mask(size, a, b, x0, y0, theta_deg):
    """
    Create a boolean mask for an ellipse within a square grid.

    The ellipse is centred at (x0, y0), has semi-axes a and b, and is
    rotated by theta_deg degrees counter-clockwise.  Co-ordinates are
    normalised so that the image spans [-1, 1] in both x and y.

    Parameters
    ----------
    size : int
        Number of pixels along one side of the square image.
    a, b : float
        Semi-axes of the ellipse (in normalised co-ordinates).
    x0, y0 : float
        Centre of the ellipse (in normalised co-ordinates).
    theta_deg : float
        Rotation angle in degrees (counter-clockwise).

    Returns
    -------
    mask : np.ndarray of bool, shape (size, size)
        True where the pixel lies inside the ellipse.
    """
    # Build a coordinate grid [-1, 1]
    coords = np.linspace(-1, 1, size)
    x, y = np.meshgrid(coords, coords)  # x varies across columns, y across rows

    # Rotate co-ordinates (inverse rotation to test membership)
    theta = np.deg2rad(theta_deg)
    cos_t, sin_t = np.cos(theta), np.sin(theta)
    x_rot = cos_t * (x - x0) + sin_t * (y - y0)
    y_rot = -sin_t * (x - x0) + cos_t * (y - y0)

    # Ellipse equation: (x'/a)² + (y'/b)² ≤ 1
    return (x_rot / a) ** 2 + (y_rot / b) ** 2 <= 1.0


def generate_shepp_logan(size=256):
    """
    Generate the modified Shepp-Logan phantom.

    The phantom is built by summing the contributions of 10 parameterised
    ellipses, each with a known additive attenuation value.  The resulting
    image has pixel values that represent the linear attenuation coefficient
    μ(x, y) in normalised units.

    Parameters
    ----------
    size : int, optional
        Image dimensions in pixels (size × size).  Default is 256.

    Returns
    -------
    phantom : np.ndarray, shape (size, size)
        The Shepp-Logan phantom image with attenuation values.

    Notes
    -----
    The standard Shepp-Logan phantom was first described in:
        Shepp, L. A. & Logan, B. F. "The Fourier Reconstruction of a Head
        Section," IEEE Trans. Nucl. Sci., 21(3):21–43, 1974.

    The modified version used here has higher contrast between structures
    to make visual assessment easier.
    """
    phantom = np.zeros((size, size), dtype=np.float64)

    for params in SHEPP_LOGAN_PARAMS:
        value, a, b, x0, y0, theta = params
        mask = _ellipse_mask(size, a, b, x0, y0, theta)
        phantom[mask] += value

    return phantom


# ---------------------------------------------------------------------------
#  QA (Quality Assurance) Phantom
# ---------------------------------------------------------------------------

def generate_qa_phantom(size=256, background_mu=0.02, verbose=False):
    """
    Generate a custom QA phantom for quantitative CT metrics evaluation.

    The phantom consists of a circular disk (simulating a water-filled
    cylinder) with several embedded inserts:

    1. **Point insert** (top-right) — a single bright pixel (or 3×3 block)
       used to measure the Point Spread Function (PSF) and derive the MTF.

    2. **Edge insert** (left side) — a sharp rectangular slab that creates
       a well-defined edge.  Used for ESF/LSF-based MTF measurement.

    3. **Low-contrast inserts** (bottom) — two circular inserts with known
       attenuation values slightly above and below background, used for CNR
       measurement.

    4. **Uniform region** (centre) — the large background area with constant
       μ, used for NPS measurement.

    Parameters
    ----------
    size : int, optional
        Image dimensions (size × size).  Default is 256.
    background_mu : float, optional
        Attenuation coefficient of the background (water-equivalent).
        Default is 0.02 mm⁻¹.
    verbose : bool, optional
        If True, print insert locations and values for debugging.

    Returns
    -------
    phantom : np.ndarray, shape (size, size)
        The QA phantom image.
    metadata : dict
        Dictionary containing the locations and attenuation values of all
        inserts, useful for automated metrics computation.

    Metadata Keys
    -------------
    - ``"background_mu"``  : background attenuation value
    - ``"point_insert"``   : dict with ``"center"``, ``"mu"``
    - ``"edge_insert"``    : dict with ``"x_range"``, ``"y_range"``, ``"mu"``
    - ``"cnr_inserts"``    : list of dicts with ``"center"``, ``"radius"``, ``"mu"``
    - ``"uniform_roi"``    : dict with ``"center"``, ``"radius"``
    """
    phantom = np.zeros((size, size), dtype=np.float64)

    # Coordinate grid normalised to [-1, 1]
    coords = np.linspace(-1, 1, size)
    x, y = np.meshgrid(coords, coords)
    r = np.sqrt(x ** 2 + y ** 2)

    # --- Outer disk (water-filled cylinder, radius = 0.9) ---
    disk_mask = r <= 0.90
    phantom[disk_mask] = background_mu

    # --- 1. Point insert (high contrast, top-right quadrant) ---
    # A small 3×3 pixel bright spot
    point_mu = background_mu + 0.05    # significantly above background
    point_center_norm = (0.35, -0.35)   # (x_norm, y_norm)  — top-right
    # Convert normalised coords to pixel indices
    pc_col = int((point_center_norm[0] + 1) / 2 * (size - 1))
    pc_row = int((point_center_norm[1] + 1) / 2 * (size - 1))
    # Place a 3×3 block
    half = 1
    r_lo, r_hi = max(pc_row - half, 0), min(pc_row + half + 1, size)
    c_lo, c_hi = max(pc_col - half, 0), min(pc_col + half + 1, size)
    phantom[r_lo:r_hi, c_lo:c_hi] = point_mu

    # --- 2. Edge insert (left side — sharp rectangular slab) ---
    edge_mu = background_mu + 0.04      # clear contrast with background
    # Slab occupies: x ∈ [-0.7, -0.3], y ∈ [-0.3, 0.3]
    edge_mask = (x >= -0.70) & (x <= -0.30) & (y >= -0.30) & (y <= 0.30) & disk_mask
    phantom[edge_mask] = edge_mu

    # --- 3. Low-contrast inserts (bottom, two circular inserts) ---
    # Insert A: slightly above background (subtle)
    insert_a_mu = background_mu + 0.005
    insert_a_center = (0.25, 0.45)  # bottom-right area
    insert_a_radius = 0.10
    dist_a = np.sqrt((x - insert_a_center[0]) ** 2 + (y - insert_a_center[1]) ** 2)
    phantom[dist_a <= insert_a_radius] = insert_a_mu

    # Insert B: slightly below background
    insert_b_mu = background_mu - 0.005
    insert_b_center = (-0.25, 0.45)  # bottom-left area -- note: there's no negative mu issue here
    # since background_mu = 0.02 > 0.005
    insert_b_radius = 0.10
    dist_b = np.sqrt((x - insert_b_center[0]) ** 2 + (y - insert_b_center[1]) ** 2)
    phantom[dist_b <= insert_b_radius] = insert_b_mu

    # --- 4. Uniform region metadata (central area) ---
    # The centre of the disk is naturally uniform — just record the ROI location
    uniform_roi_center = (0.0, 0.0)
    uniform_roi_radius = 0.15

    # --- Build metadata ---
    metadata = {
        "size": size,
        "background_mu": background_mu,
        "disk_radius": 0.90,
        "point_insert": {
            "center_pixel": (pc_row, pc_col),
            "center_norm": point_center_norm,
            "mu": point_mu,
            "description": "3×3 bright spot for PSF/MTF measurement",
        },
        "edge_insert": {
            "x_range_norm": (-0.70, -0.30),
            "y_range_norm": (-0.30, 0.30),
            "mu": edge_mu,
            "description": "Rectangular slab for ESF/LSF-based MTF measurement",
        },
        "cnr_inserts": [
            {
                "label": "Insert A (above background)",
                "center_norm": insert_a_center,
                "radius_norm": insert_a_radius,
                "mu": insert_a_mu,
            },
            {
                "label": "Insert B (below background)",
                "center_norm": insert_b_center,
                "radius_norm": insert_b_radius,
                "mu": insert_b_mu,
            },
        ],
        "uniform_roi": {
            "center_norm": uniform_roi_center,
            "radius_norm": uniform_roi_radius,
            "description": "Central uniform region for NPS measurement",
        },
    }

    if verbose:
        print("=== QA Phantom Metadata ===")
        print(f"  Background μ = {background_mu}")
        print(f"  Point insert: centre pixel ({pc_row}, {pc_col}), μ = {point_mu}")
        print(f"  Edge insert: μ = {edge_mu}")
        for ins in metadata["cnr_inserts"]:
            print(f"  {ins['label']}: centre {ins['center_norm']}, "
                  f"radius {ins['radius_norm']}, μ = {ins['mu']}")

    return phantom, metadata


# ---------------------------------------------------------------------------
#  Convenience / utility functions
# ---------------------------------------------------------------------------

def norm_to_pixel(center_norm, size):
    """
    Convert normalised coordinates (-1..1) to pixel indices.

    Parameters
    ----------
    center_norm : tuple of float
        (x_norm, y_norm) in the range [-1, 1].
    size : int
        Image size (pixels per side).

    Returns
    -------
    (row, col) : tuple of int
    """
    col = int((center_norm[0] + 1) / 2 * (size - 1))
    row = int((center_norm[1] + 1) / 2 * (size - 1))
    return row, col


def pixel_to_norm(row, col, size):
    """
    Convert pixel indices to normalised coordinates (-1..1).

    Parameters
    ----------
    row, col : int
        Pixel indices.
    size : int
        Image size (pixels per side).

    Returns
    -------
    (x_norm, y_norm) : tuple of float
    """
    x_norm = 2 * col / (size - 1) - 1
    y_norm = 2 * row / (size - 1) - 1
    return x_norm, y_norm
