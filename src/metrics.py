"""
Basic Image Quality Metrics — Phase 5 (Ammar Yasser)
=====================================================

Implements standard image quality metrics for comparing reconstructed
CT images against ground truth (the original phantom).  These metrics
complement the system-level metrics (MTF, NPS, CNR) by providing
simple, scalar summaries of reconstruction accuracy.

Metrics Implemented
-------------------

1. **RMSE (Root Mean Square Error)**:

       RMSE = √[ (1/N) · Σ (x_i − y_i)² ]

   Measures the average magnitude of pixel-wise errors.  Lower is better.
   Units are the same as the image values (attenuation coefficient).
   Limitation: RMSE is dominated by large errors and doesn't account
   for structural information.

2. **SSIM (Structural Similarity Index)**:

       SSIM(x, y) = [(2·μ_x·μ_y + C₁)(2·σ_xy + C₂)]
                    / [(μ_x² + μ_y² + C₁)(σ_x² + σ_y² + C₂)]

   Measures structural similarity, accounting for luminance, contrast,
   and structure.  Range: [−1, 1], where 1 = perfect similarity.
   C₁ and C₂ are small constants for numerical stability.
   Advantage over RMSE: better correlates with human visual perception.

3. **SNR (Signal-to-Noise Ratio)**:

       SNR = μ_signal / σ_noise

   or in dB:

       SNR_dB = 20 · log₁₀(μ_signal / σ_noise)

   Measures how much the signal stands above the noise floor.
   Higher is better.

4. **PSNR (Peak Signal-to-Noise Ratio)**:

       PSNR = 20 · log₁₀(MAX_val / RMSE)

   Variant of SNR that uses the peak possible value instead of the
   mean.  Common in image processing literature.

Limitations
-----------
These are all **global, scalar** metrics.  They cannot distinguish
between different types of degradation (blur vs. noise vs. artifacts).
The frequency-domain metrics (MTF, NPS) and task-specific metrics (CNR)
provide much richer characterisation.  These basic metrics are still
useful for quick comparisons and sanity checks.
"""

import numpy as np


def compute_rmse(image, reference):
    """
    Compute Root Mean Square Error between two images.

        RMSE = √[ (1/N) · Σ (image_i − reference_i)² ]

    Parameters
    ----------
    image : np.ndarray
        Reconstructed image.
    reference : np.ndarray
        Ground truth (phantom) image.  Must be same shape as ``image``.

    Returns
    -------
    rmse : float
        The RMSE value.  Lower is better.
    """
    diff = image.astype(np.float64) - reference.astype(np.float64)
    return np.sqrt(np.mean(diff ** 2))


def compute_ssim(image, reference, C1=None, C2=None, window_size=7):
    """
    Compute the Structural Similarity Index (SSIM).

    Uses a sliding-window approach to compute local SSIM values, then
    averages them to produce the overall SSIM.

    Parameters
    ----------
    image : np.ndarray
        Reconstructed image.
    reference : np.ndarray
        Ground truth image.
    C1 : float or None, optional
        Luminance stability constant.  If None, set to (0.01 · L)²
        where L is the dynamic range of the reference.
    C2 : float or None, optional
        Contrast stability constant.  If None, set to (0.03 · L)².
    window_size : int, optional
        Size of the sliding window (must be odd).  Default is 7.

    Returns
    -------
    ssim_value : float
        Mean SSIM over all windows.  Range: [−1, 1], 1 = perfect.
    ssim_map : np.ndarray
        Local SSIM map (same shape as input, padded regions are NaN).

    Notes
    -----
    This is a simplified implementation using a uniform (box) window.
    The original SSIM paper by Wang et al. (2004) uses a Gaussian window,
    but the uniform window gives qualitatively similar results for our
    purposes.

    Reference:
        Wang, Z., Bovik, A. C., Sheikh, H. R., & Simoncelli, E. P.
        "Image Quality Assessment: From Error Visibility to Structural
        Similarity," IEEE TIP, 13(4):600–612, 2004.
    """
    img = image.astype(np.float64)
    ref = reference.astype(np.float64)

    # Dynamic range
    L = ref.max() - ref.min()
    if L == 0:
        L = 1.0

    if C1 is None:
        C1 = (0.01 * L) ** 2
    if C2 is None:
        C2 = (0.03 * L) ** 2

    # Pad to handle window
    half_w = window_size // 2
    rows, cols = img.shape

    ssim_map = np.full_like(img, np.nan)

    for i in range(half_w, rows - half_w):
        for j in range(half_w, cols - half_w):
            # Extract windows
            win_img = img[i - half_w:i + half_w + 1, j - half_w:j + half_w + 1]
            win_ref = ref[i - half_w:i + half_w + 1, j - half_w:j + half_w + 1]

            mu_x = np.mean(win_img)
            mu_y = np.mean(win_ref)
            sigma_x2 = np.var(win_img)
            sigma_y2 = np.var(win_ref)
            sigma_xy = np.mean((win_img - mu_x) * (win_ref - mu_y))

            numerator = (2 * mu_x * mu_y + C1) * (2 * sigma_xy + C2)
            denominator = (mu_x ** 2 + mu_y ** 2 + C1) * (sigma_x2 + sigma_y2 + C2)

            ssim_map[i, j] = numerator / denominator

    ssim_value = np.nanmean(ssim_map)

    return ssim_value, ssim_map


def compute_snr(image, signal_roi=None, noise_roi=None):
    """
    Compute Signal-to-Noise Ratio.

        SNR = μ_signal / σ_noise

    Parameters
    ----------
    image : np.ndarray
        Reconstructed image.
    signal_roi : np.ndarray or None, optional
        Boolean mask for the signal region.  If None, the entire image
        is used as the signal (mean of whole image).
    noise_roi : np.ndarray or None, optional
        Boolean mask for the noise region.  If None, same region as
        signal_roi is used (noise = std of signal region).

    Returns
    -------
    snr : float
        Signal-to-noise ratio.
    snr_db : float
        SNR in decibels: 20·log₁₀(SNR).
    """
    if signal_roi is not None:
        signal_values = image[signal_roi]
    else:
        signal_values = image.ravel()

    if noise_roi is not None:
        noise_values = image[noise_roi]
    else:
        noise_values = signal_values

    mu = np.mean(signal_values)
    sigma = np.std(noise_values)

    if sigma > 0:
        snr = mu / sigma
        snr_db = 20 * np.log10(np.abs(snr))
    else:
        snr = np.inf
        snr_db = np.inf

    return snr, snr_db


def compute_psnr(image, reference):
    """
    Compute Peak Signal-to-Noise Ratio.

        PSNR = 20 · log₁₀(MAX / RMSE)

    Parameters
    ----------
    image : np.ndarray
        Reconstructed image.
    reference : np.ndarray
        Ground truth image.

    Returns
    -------
    psnr : float
        PSNR in decibels.  Higher is better.
    """
    rmse = compute_rmse(image, reference)
    if rmse == 0:
        return np.inf

    max_val = np.max(np.abs(reference))
    if max_val == 0:
        max_val = 1.0

    return 20 * np.log10(max_val / rmse)


def compute_all_metrics(image, reference):
    """
    Compute all basic image quality metrics at once.

    Parameters
    ----------
    image : np.ndarray
        Reconstructed image.
    reference : np.ndarray
        Ground truth image (same shape).

    Returns
    -------
    metrics : dict
        Dictionary with keys:
        - ``"rmse"`` : Root Mean Square Error
        - ``"ssim"`` : Structural Similarity Index
        - ``"snr"`` : Signal-to-Noise Ratio
        - ``"snr_db"`` : SNR in dB
        - ``"psnr"`` : Peak Signal-to-Noise Ratio (dB)
    """
    rmse = compute_rmse(image, reference)
    ssim_val, _ = compute_ssim(image, reference)
    snr, snr_db = compute_snr(image)
    psnr = compute_psnr(image, reference)

    return {
        "rmse": rmse,
        "ssim": ssim_val,
        "snr": snr,
        "snr_db": snr_db,
        "psnr": psnr,
    }


def metrics_comparison_table(metrics_dict):
    """
    Format a dictionary of metrics into a printable comparison table.

    Parameters
    ----------
    metrics_dict : dict
        Dictionary mapping condition labels to metric dicts.
        e.g., {"360 angles": {"rmse": 0.01, "ssim": 0.95, ...}, ...}

    Returns
    -------
    table_str : str
        Formatted table string.
    """
    if not metrics_dict:
        return "No metrics to display."

    # Get metric names from the first entry
    first_key = next(iter(metrics_dict))
    metric_names = list(metrics_dict[first_key].keys())

    # Header
    header = f"{'Condition':<25} " + " ".join(f"{m:>12}" for m in metric_names)
    separator = "-" * len(header)

    rows = [header, separator]
    for label, metrics in metrics_dict.items():
        values = " ".join(f"{metrics[m]:>12.6f}" for m in metric_names)
        rows.append(f"{label:<25} {values}")

    return "\n".join(rows)
