"""
Shared Utilities — Phase 5 (Ammar Yasser)
===========================================

Provides display, I/O, ROI extraction, and plotting utilities shared
across all modules.  Designed for producing publication-quality figures
suitable for the final presentation and report.
"""

import numpy as np
import os


# ---------------------------------------------------------------------------
#  ROI Extraction Helpers
# ---------------------------------------------------------------------------

def extract_circular_roi(image, center, radius, coordinate_system="pixel"):
    """
    Extract pixel values within a circular ROI.

    Parameters
    ----------
    image : np.ndarray, shape (N, N)
        Input image.
    center : tuple
        (row, col) in pixel coords, or (x_norm, y_norm) in normalised.
    radius : float
        ROI radius (pixel or normalised units).
    coordinate_system : str
        ``"pixel"`` or ``"norm"``.

    Returns
    -------
    values : np.ndarray
        1D array of pixel values inside the ROI.
    mask : np.ndarray, shape (N, N)
        Boolean mask of the ROI.
    """
    N = image.shape[0]

    if coordinate_system == "norm":
        cx, cy = center
        col_c = (cx + 1) / 2 * (N - 1)
        row_c = (cy + 1) / 2 * (N - 1)
        r_pix = radius / 2 * (N - 1)
    else:
        row_c, col_c = center
        r_pix = radius

    rows, cols = np.ogrid[:N, :N]
    dist = np.sqrt((rows - row_c) ** 2 + (cols - col_c) ** 2)
    mask = dist <= r_pix

    return image[mask], mask


def extract_rectangular_roi(image, top_left, bottom_right):
    """
    Extract pixel values within a rectangular ROI.

    Parameters
    ----------
    image : np.ndarray
        Input image.
    top_left : tuple of int
        (row, col) of the top-left corner.
    bottom_right : tuple of int
        (row, col) of the bottom-right corner.

    Returns
    -------
    roi : np.ndarray
        The extracted rectangular region.
    """
    r1, c1 = top_left
    r2, c2 = bottom_right
    return image[r1:r2, c1:c2].copy()


# ---------------------------------------------------------------------------
#  Display Utilities (Matplotlib-based)
# ---------------------------------------------------------------------------

def display_image(image, title="", cmap="gray", colorbar=True,
                  figsize=(6, 6), vmin=None, vmax=None, save_path=None):
    """
    Display a single image with a colorbar and title.

    Parameters
    ----------
    image : np.ndarray
        2D image to display.
    title : str
        Figure title.
    cmap : str
        Colormap name.
    colorbar : bool
        Whether to show a colorbar.
    figsize : tuple
        Figure size in inches.
    vmin, vmax : float or None
        Color scale limits.
    save_path : str or None
        If given, save the figure to this path.
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 1, figsize=figsize)
    im = ax.imshow(image, cmap=cmap, vmin=vmin, vmax=vmax)
    ax.set_title(title, fontsize=14)
    ax.axis("off")
    if colorbar:
        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved: {save_path}")

    plt.show()


def display_images_grid(images, titles=None, ncols=3, cmap="gray",
                        figsize=None, suptitle=None, colorbar=True,
                        vmin=None, vmax=None, save_path=None):
    """
    Display multiple images in a grid layout.

    Parameters
    ----------
    images : list of np.ndarray
        List of 2D images.
    titles : list of str or None
        Titles for each subplot.
    ncols : int
        Number of columns in the grid.
    cmap : str
        Colormap.
    figsize : tuple or None
        Figure size.  If None, auto-computed.
    suptitle : str or None
        Overall figure title.
    colorbar : bool
        Show colorbars.
    vmin, vmax : float or None
        Color scale limits (applied to all images).
    save_path : str or None
        Save path.
    """
    import matplotlib.pyplot as plt

    n = len(images)
    nrows = int(np.ceil(n / ncols))
    if figsize is None:
        figsize = (5 * ncols, 4.5 * nrows)

    fig, axes = plt.subplots(nrows, ncols, figsize=figsize)
    if nrows == 1 and ncols == 1:
        axes = np.array([axes])
    axes = axes.ravel()

    for i, img in enumerate(images):
        im = axes[i].imshow(img, cmap=cmap, vmin=vmin, vmax=vmax)
        if titles and i < len(titles):
            axes[i].set_title(titles[i], fontsize=11)
        axes[i].axis("off")
        if colorbar:
            plt.colorbar(im, ax=axes[i], fraction=0.046, pad=0.04)

    # Hide unused subplots
    for i in range(n, len(axes)):
        axes[i].set_visible(False)

    if suptitle:
        fig.suptitle(suptitle, fontsize=16, fontweight="bold")

    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved: {save_path}")

    plt.show()


def display_sinogram(sinogram, angles=None, title="Sinogram",
                     save_path=None):
    """
    Display a sinogram with properly labelled axes.

    Parameters
    ----------
    sinogram : np.ndarray, shape (num_detectors, num_angles)
        The sinogram.
    angles : np.ndarray or None
        Projection angles.  If None, uses column indices.
    title : str
        Figure title.
    save_path : str or None
        Save path.
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 1, figsize=(10, 6))

    extent = None
    if angles is not None:
        extent = [angles[0], angles[-1], sinogram.shape[0] - 1, 0]

    im = ax.imshow(sinogram, cmap="hot", aspect="auto", extent=extent)
    ax.set_xlabel("Projection Angle (°)" if angles is not None else "Angle Index",
                  fontsize=12)
    ax.set_ylabel("Detector Position", fontsize=12)
    ax.set_title(title, fontsize=14)
    plt.colorbar(im, ax=ax, label="Line Integral Value")
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved: {save_path}")

    plt.show()


def plot_mtf_curves(freq_mtf_pairs, title="MTF Comparison",
                    xlabel="Spatial Frequency (cycles/pixel)",
                    ylabel="MTF", save_path=None):
    """
    Plot multiple MTF curves on the same axes.

    Parameters
    ----------
    freq_mtf_pairs : dict
        Mapping label → (freq_array, mtf_array).
    title : str
        Plot title.
    xlabel, ylabel : str
        Axis labels.
    save_path : str or None
        Save path.
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 1, figsize=(8, 5))

    for label, (freq, mtf) in freq_mtf_pairs.items():
        ax.plot(freq, mtf, label=label, linewidth=2)

    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(fontsize=10)
    ax.set_ylim(-0.05, 1.1)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved: {save_path}")

    plt.show()


def plot_nps_curves(freq_nps_pairs, title="NPS Comparison",
                    xlabel="Spatial Frequency (cycles/pixel)",
                    ylabel="NPS", log_scale=True, save_path=None):
    """
    Plot multiple NPS curves on the same axes.

    Parameters
    ----------
    freq_nps_pairs : dict
        Mapping label → (freq_array, nps_array).
    title, xlabel, ylabel : str
        Plot labels.
    log_scale : bool
        If True, use log scale on the y-axis.
    save_path : str or None
        Save path.
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 1, figsize=(8, 5))

    for label, (freq, nps_vals) in freq_nps_pairs.items():
        ax.plot(freq, nps_vals, label=label, linewidth=2)

    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14)
    ax.legend(fontsize=10)
    if log_scale:
        ax.set_yscale("log")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved: {save_path}")

    plt.show()


def plot_metric_vs_parameter(param_values, metric_values, param_name,
                              metric_name, title=None, log_x=False,
                              save_path=None):
    """
    Plot a single metric as a function of a parameter.

    Parameters
    ----------
    param_values : array-like
        X-axis values (e.g., dose levels, number of projections).
    metric_values : array-like
        Y-axis values (the metric).
    param_name : str
        Label for x-axis.
    metric_name : str
        Label for y-axis.
    title : str or None
        Plot title.
    log_x : bool
        Use log scale for x-axis.
    save_path : str or None
        Save path.
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 1, figsize=(8, 5))
    ax.plot(param_values, metric_values, "o-", linewidth=2, markersize=8)
    ax.set_xlabel(param_name, fontsize=12)
    ax.set_ylabel(metric_name, fontsize=12)
    if title:
        ax.set_title(title, fontsize=14)
    if log_x:
        ax.set_xscale("log")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved: {save_path}")

    plt.show()


# ---------------------------------------------------------------------------
#  I/O Utilities
# ---------------------------------------------------------------------------

def save_results(results_dict, filepath):
    """
    Save a results dictionary to a .npz file.

    Parameters
    ----------
    results_dict : dict
        Dictionary of numpy arrays and scalars.
    filepath : str
        Output path (should end with .npz).
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    np.savez(filepath, **results_dict)
    print(f"Results saved to {filepath}")


def load_results(filepath):
    """
    Load results from a .npz file.

    Parameters
    ----------
    filepath : str
        Path to the .npz file.

    Returns
    -------
    data : dict
        Dictionary of loaded arrays.
    """
    data = np.load(filepath, allow_pickle=True)
    return dict(data)


def ensure_dir(path):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)
