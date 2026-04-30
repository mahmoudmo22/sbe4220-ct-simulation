"""
Contrast-to-Noise Ratio (CNR) — Phase 4 (Rashed Mamdouh)
==========================================================

Implements CNR measurement for quantifying object detectability in
reconstructed CT images.

Physics Background
------------------
CNR (Contrast-to-Noise Ratio) is the most clinically intuitive of the
three performance metrics.  It answers the fundamental question:

    "Can the observer distinguish this object (e.g., a tumour) from the
     surrounding tissue?"

The CNR is defined as:

    CNR = |μ_insert − μ_background| / σ_background

where:
    μ_insert      = mean attenuation in the object/insert ROI
    μ_background  = mean attenuation in the background ROI
    σ_background  = standard deviation (noise) in the background ROI

The Rose Criterion
------------------
The Rose criterion states that an object can be reliably detected by a
human observer when CNR ≥ 3–5.  Below this threshold, the object's
contrast is buried in the noise fluctuations and becomes statistically
indistinguishable from random noise patterns.

Factors Affecting CNR
---------------------
CNR depends on:
1. **Contrast**: |μ_insert − μ_background| — determined by tissue
   properties (not under our control in clinical practice).
2. **Noise level**: σ_background — determined by:
   - Dose (I₀): σ ∝ 1/√I₀, so CNR ∝ √I₀.
   - Filter choice: smoother filters reduce σ but also reduce MTF.
   - Number of projections: more projections reduce noise.

This means:
- Doubling the dose improves CNR by √2 ≈ 1.41.
- Using a smoother filter improves CNR (lower σ) but at the cost of
  spatial resolution (lower MTF at high frequencies).
- There is ALWAYS a trade-off between CNR (detectability) and MTF
  (resolution).
"""

import numpy as np


def measure_roi_statistics(image, center, radius, coordinate_system="pixel"):
    """
    Compute mean and standard deviation within a circular ROI.

    Parameters
    ----------
    image : np.ndarray, shape (N, N)
        Reconstructed image.
    center : tuple
        Centre of the ROI.  Interpretation depends on ``coordinate_system``.
    radius : float
        Radius of the ROI.  Same units as ``center``.
    coordinate_system : str, optional
        ``"pixel"`` — centre and radius are in pixel coordinates.
        ``"norm"`` — centre and radius are in normalised coordinates
        (−1 to 1).

    Returns
    -------
    stats : dict
        - ``"mean"`` : mean pixel value within the ROI.
        - ``"std"`` : standard deviation within the ROI.
        - ``"num_pixels"`` : number of pixels in the ROI.
        - ``"values"`` : the actual pixel values (1D array).
    """
    N = image.shape[0]

    if coordinate_system == "norm":
        # Convert normalised → pixel
        cx_norm, cy_norm = center
        col_c = (cx_norm + 1) / 2 * (N - 1)
        row_c = (cy_norm + 1) / 2 * (N - 1)
        r_pix = radius / 2 * (N - 1)
    else:
        row_c, col_c = center
        r_pix = radius

    # Create mask for circular ROI
    rows, cols = np.ogrid[:N, :N]
    dist = np.sqrt((rows - row_c) ** 2 + (cols - col_c) ** 2)
    mask = dist <= r_pix

    values = image[mask]

    return {
        "mean": np.mean(values),
        "std": np.std(values),
        "num_pixels": len(values),
        "values": values,
    }


def compute_cnr(image, insert_center, insert_radius,
                bg_center, bg_radius,
                coordinate_system="pixel"):
    """
    Compute the Contrast-to-Noise Ratio between an insert and background.

        CNR = |μ_insert − μ_background| / σ_background

    Parameters
    ----------
    image : np.ndarray, shape (N, N)
        Reconstructed image.
    insert_center : tuple
        Centre of the insert ROI.
    insert_radius : float
        Radius of the insert ROI.
    bg_center : tuple
        Centre of the background ROI.
    bg_radius : float
        Radius of the background ROI.
    coordinate_system : str, optional
        ``"pixel"`` or ``"norm"`` (normalised −1 to 1).

    Returns
    -------
    cnr_value : float
        The computed CNR.
    details : dict
        - ``"insert_mean"`` : mean of the insert ROI.
        - ``"bg_mean"`` : mean of the background ROI.
        - ``"bg_std"`` : noise (σ) of the background ROI.
        - ``"contrast"`` : |μ_insert − μ_background|.
        - ``"rose_detectable"`` : bool — whether CNR ≥ 3 (Rose criterion).

    Example
    -------
    >>> cnr, info = compute_cnr(recon,
    ...     insert_center=(0.25, 0.45), insert_radius=0.08,
    ...     bg_center=(0.0, 0.0), bg_radius=0.10,
    ...     coordinate_system="norm")
    >>> print(f"CNR = {cnr:.2f}, detectable = {info['rose_detectable']}")
    """
    insert_stats = measure_roi_statistics(
        image, insert_center, insert_radius, coordinate_system
    )
    bg_stats = measure_roi_statistics(
        image, bg_center, bg_radius, coordinate_system
    )

    contrast = np.abs(insert_stats["mean"] - bg_stats["mean"])
    bg_std = bg_stats["std"]

    if bg_std > 0:
        cnr_value = contrast / bg_std
    else:
        cnr_value = np.inf  # no noise → infinite CNR

    details = {
        "insert_mean": insert_stats["mean"],
        "bg_mean": bg_stats["mean"],
        "bg_std": bg_std,
        "contrast": contrast,
        "cnr": cnr_value,
        "rose_detectable": cnr_value >= 3.0,
        "insert_num_pixels": insert_stats["num_pixels"],
        "bg_num_pixels": bg_stats["num_pixels"],
    }

    return cnr_value, details


def compute_cnr_from_qa_phantom(image, qa_metadata, insert_index=0):
    """
    Compute CNR using the QA phantom metadata for automatic ROI placement.

    Uses the insert and background locations stored in the QA phantom
    metadata dictionary (from ``phantom.generate_qa_phantom``).

    Parameters
    ----------
    image : np.ndarray, shape (N, N)
        Reconstructed image of the QA phantom.
    qa_metadata : dict
        Metadata dictionary from ``generate_qa_phantom``.
    insert_index : int, optional
        Which CNR insert to use (0 or 1).  Default is 0.

    Returns
    -------
    cnr_value : float
        The computed CNR.
    details : dict
        Same as ``compute_cnr``, plus ``"expected_contrast"`` from metadata.
    """
    insert_info = qa_metadata["cnr_inserts"][insert_index]
    bg_mu = qa_metadata["background_mu"]

    # Insert ROI
    insert_center = insert_info["center_norm"]
    insert_radius = insert_info["radius_norm"] * 0.7  # Use 70% to stay inside

    # Background ROI — use the uniform region
    bg_center = qa_metadata["uniform_roi"]["center_norm"]
    bg_radius = qa_metadata["uniform_roi"]["radius_norm"] * 0.7

    cnr_value, details = compute_cnr(
        image,
        insert_center=insert_center,
        insert_radius=insert_radius,
        bg_center=bg_center,
        bg_radius=bg_radius,
        coordinate_system="norm",
    )

    # Add expected contrast from phantom design
    details["expected_contrast"] = np.abs(insert_info["mu"] - bg_mu)
    details["insert_label"] = insert_info["label"]

    return cnr_value, details


def cnr_vs_dose(image_dict, qa_metadata, insert_index=0):
    """
    Compute CNR for multiple dose levels.

    Parameters
    ----------
    image_dict : dict
        Dictionary mapping dose level (I₀) to reconstructed images.
        e.g., {1e6: recon_1e6, 1e5: recon_1e5, ...}
    qa_metadata : dict
        QA phantom metadata.
    insert_index : int, optional
        Which CNR insert to use.

    Returns
    -------
    doses : np.ndarray
        Array of dose levels.
    cnr_values : np.ndarray
        Array of corresponding CNR values.
    all_details : dict
        Full details for each dose level.

    Notes
    -----
    We expect CNR ∝ √I₀.  Plotting CNR vs √I₀ should give a linear
    relationship.
    """
    doses = sorted(image_dict.keys())
    cnr_values = []
    all_details = {}

    for I0 in doses:
        cnr_val, details = compute_cnr_from_qa_phantom(
            image_dict[I0], qa_metadata, insert_index
        )
        cnr_values.append(cnr_val)
        all_details[I0] = details

    return np.array(doses), np.array(cnr_values), all_details


def rose_criterion_dose(cnr_values, doses, target_cnr=3.0):
    """
    Estimate the minimum dose required to achieve the Rose criterion.

    Uses linear interpolation on CNR vs √dose data.

    Parameters
    ----------
    cnr_values : np.ndarray
        CNR values at each dose level.
    doses : np.ndarray
        Corresponding dose levels.
    target_cnr : float, optional
        Target CNR threshold.  Default is 3.0 (Rose criterion).

    Returns
    -------
    min_dose : float or None
        Estimated minimum dose for CNR ≥ target_cnr, or None if the
        target is never reached.
    """
    # Sort by dose
    order = np.argsort(doses)
    doses_sorted = doses[order]
    cnr_sorted = cnr_values[order]

    if np.all(cnr_sorted >= target_cnr):
        return doses_sorted[0]  # always above threshold
    if np.all(cnr_sorted < target_cnr):
        return None  # never reaches threshold

    # Find crossing point via interpolation
    for i in range(len(cnr_sorted) - 1):
        if cnr_sorted[i] < target_cnr <= cnr_sorted[i + 1]:
            # Linear interpolation
            frac = (target_cnr - cnr_sorted[i]) / (cnr_sorted[i + 1] - cnr_sorted[i])
            min_dose = doses_sorted[i] + frac * (doses_sorted[i + 1] - doses_sorted[i])
            return min_dose

    return None
