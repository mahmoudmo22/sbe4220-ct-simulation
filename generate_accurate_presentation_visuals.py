import os
import sys

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Rectangle
from matplotlib.transforms import Affine2D

sys.path.append(os.path.abspath("src"))

from cnr import compute_cnr_from_qa_phantom
from fbp import AVAILABLE_FILTERS, reconstruct_fbp
from forward_projection import generate_sinogram_fast
from mtf import compute_mtf_from_reconstruction
from noise_model import add_poisson_noise
from nps import compute_nps
from phantom import generate_qa_phantom, norm_to_pixel
from metrics import compute_rmse, compute_ssim


OUTPUT_DIR = os.path.join("presentation", "visuals")
SIZE = 256
BASE_ANGLES = 180
QA_VMIN = 0.0
QA_VMAX = 0.08


def savefig(path):
    plt.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches="tight", facecolor=plt.gcf().get_facecolor())
    plt.close()
    print(f"Saved {path}")


def normalized_edge_col(metadata, image_size):
    edge_x = metadata["edge_insert"]["x_range_norm"][1]
    return int((edge_x + 1.0) / 2.0 * (image_size - 1))


def add_qa_overlays(ax, metadata, image_size):
    edge = metadata["edge_insert"]
    edge_x = edge["x_range_norm"][1]
    edge_col = (edge_x + 1.0) / 2.0 * (image_size - 1)
    edge_row_0 = (edge["y_range_norm"][0] + 1.0) / 2.0 * (image_size - 1)
    edge_row_1 = (edge["y_range_norm"][1] + 1.0) / 2.0 * (image_size - 1)
    ax.plot(
        [edge_col, edge_col],
        [edge_row_0, edge_row_1],
        color="cyan",
        linewidth=3,
        label="MTF edge",
    )

    insert = metadata["cnr_inserts"][0]
    insert_row, insert_col = norm_to_pixel(insert["center_norm"], image_size)
    insert_radius = insert["radius_norm"] * 0.7 / 2.0 * (image_size - 1)
    ax.add_patch(
        Circle(
            (insert_col, insert_row),
            insert_radius,
            fill=False,
            edgecolor="lime",
            linewidth=3,
            label="CNR insert",
        )
    )

    uniform = metadata["uniform_roi"]
    bg_row, bg_col = norm_to_pixel(uniform["center_norm"], image_size)
    bg_radius = uniform["radius_norm"] * 0.7 / 2.0 * (image_size - 1)
    ax.add_patch(
        Circle(
            (bg_col, bg_row),
            bg_radius,
            fill=False,
            edgecolor="yellow",
            linewidth=3,
            label="CNR background",
        )
    )

    roi_size = 32
    ax.add_patch(
        Rectangle(
            (bg_col - roi_size / 2, bg_row - roi_size / 2),
            roi_size,
            roi_size,
            fill=False,
            edgecolor="magenta",
            linewidth=2.5,
            linestyle="--",
            label="NPS ROI",
        )
    )


def generate_slide_2_visuals(qa_phantom):
    plt.figure(figsize=(6, 6))
    plt.imshow(qa_phantom, cmap="gray", vmin=QA_VMIN, vmax=QA_VMAX)
    plt.title("2D QA Phantom", fontsize=16)
    plt.axis("off")
    plt.colorbar(label="Attenuation coefficient")
    savefig(os.path.join(OUTPUT_DIR, "slide02_qa_phantom.png"))

    fig, axes = plt.subplots(2, 2, figsize=(10, 10), facecolor="black")
    angles = [0, 45, 90, 135]
    for ax, angle in zip(axes.ravel(), angles):
        ax.imshow(qa_phantom, cmap="gray", vmin=QA_VMIN, vmax=QA_VMAX)
        transform = Affine2D().rotate_deg_around(SIZE / 2, SIZE / 2, -angle) + ax.transData
        for x_pos in np.linspace(24, SIZE - 24, 18):
            ax.plot(
                [x_pos, x_pos],
                [0, SIZE],
                color="red",
                alpha=0.65,
                linewidth=1.5,
                transform=transform,
            )
        ax.axis("off")
    plt.subplots_adjust(wspace=0.02, hspace=0.02)
    savefig(os.path.join(OUTPUT_DIR, "slide02_parallel_beam_overlay.png"))


def generate_slide_3_visuals(qa_phantom):
    clean_sino, angles = generate_sinogram_fast(qa_phantom, BASE_ANGLES)
    recon = reconstruct_fbp(clean_sino, angles, filter_name="ram-lak")
    error = recon - qa_phantom

    plt.figure(figsize=(7, 5))
    plt.imshow(clean_sino, cmap="hot", aspect="auto")
    plt.title("Clean Sinogram (Radon Transform)", fontsize=16)
    plt.xlabel("Projection angle index")
    plt.ylabel("Detector bin")
    plt.colorbar(label="Line integral")
    savefig(os.path.join(OUTPUT_DIR, "slide03_clean_sinogram.png"))

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    axes[0].imshow(qa_phantom, cmap="gray", vmin=QA_VMIN, vmax=QA_VMAX)
    axes[0].set_title("Ground Truth")
    axes[1].imshow(recon, cmap="gray", vmin=QA_VMIN, vmax=QA_VMAX)
    axes[1].set_title("FBP Reconstruction")
    err_lim = np.percentile(np.abs(error), 99)
    axes[2].imshow(error, cmap="seismic", vmin=-err_lim, vmax=err_lim)
    axes[2].set_title("Reconstruction Error")
    for ax in axes:
        ax.axis("off")
    savefig(os.path.join(OUTPUT_DIR, "slide03_fbp_reconstruction_comparison.png"))

    plt.figure(figsize=(6, 6))
    plt.imshow(recon, cmap="gray", vmin=QA_VMIN, vmax=QA_VMAX)
    plt.title("FBP Reconstruction (Ram-Lak)", fontsize=16)
    plt.axis("off")
    plt.colorbar(label="Attenuation coefficient")
    savefig(os.path.join(OUTPUT_DIR, "slide03_reconstructed_image.png"))

    return clean_sino, angles


def generate_slide_4_visuals(clean_sino):
    high_dose = 1e6
    low_dose = 1e3
    high_sino, _ = add_poisson_noise(clean_sino, high_dose, rng=42)
    low_sino, _ = add_poisson_noise(clean_sino, low_dose, rng=42)

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    vmin = min(high_sino.min(), low_sino.min())
    vmax = max(high_sino.max(), low_sino.max())
    im0 = axes[0].imshow(high_sino, cmap="hot", aspect="auto", vmin=vmin, vmax=vmax)
    axes[0].set_title("High Dose Sinogram (I0 = 1e6)", fontsize=14)
    axes[0].set_xlabel("Angle index")
    axes[0].set_ylabel("Detector bin")
    axes[1].imshow(low_sino, cmap="hot", aspect="auto", vmin=vmin, vmax=vmax)
    axes[1].set_title("Low Dose Sinogram (I0 = 1e3)", fontsize=14)
    axes[1].set_xlabel("Angle index")
    axes[1].set_ylabel("Detector bin")
    fig.colorbar(im0, ax=axes.ravel().tolist(), label="Line integral")
    savefig(os.path.join(OUTPUT_DIR, "slide04_high_vs_low_dose_sinograms.png"))


def generate_slide_5_visuals():
    qa_phantom, metadata = generate_qa_phantom(SIZE)
    plt.figure(figsize=(7, 7))
    ax = plt.gca()
    im = ax.imshow(qa_phantom, cmap="gray", vmin=QA_VMIN, vmax=QA_VMAX)
    add_qa_overlays(ax, metadata, SIZE)
    ax.set_title("QA Phantom Metric Regions", fontsize=16)
    ax.axis("off")
    ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
    plt.colorbar(im, ax=ax, label="Attenuation coefficient")
    savefig(os.path.join(OUTPUT_DIR, "slide05_qa_phantom_metric_regions.png"))
    return qa_phantom, metadata


def generate_slide_6_visuals(qa_phantom, metadata):
    sino, angles = generate_sinogram_fast(qa_phantom, BASE_ANGLES)
    noisy_sino, _ = add_poisson_noise(sino, 1e5, rng=42)
    edge_col = normalized_edge_col(metadata, SIZE)

    mtf_results = {}
    nps_results = {}
    for filter_name in AVAILABLE_FILTERS:
        # Use clean data for MTF so the plot isolates the filter's resolution effect.
        recon_clean = reconstruct_fbp(sino, angles, filter_name=filter_name)
        freq_mtf, mtf_vals = compute_mtf_from_reconstruction(
            recon_clean, method="edge", edge_col=edge_col
        )

        # Use noisy data for NPS because NPS characterizes noise texture.
        recon_noisy = reconstruct_fbp(noisy_sino, angles, filter_name=filter_name)
        freq_nps, nps_vals, _, _ = compute_nps(
            recon_noisy, roi_size=32, num_rois=8, center=(SIZE // 2, SIZE // 2)
        )
        mtf_results[filter_name] = (freq_mtf, mtf_vals)
        nps_results[filter_name] = (freq_nps, nps_vals)

    plt.figure(figsize=(8, 5))
    for label, (freq, mtf) in mtf_results.items():
        plt.plot(freq, mtf, linewidth=2, label=label)
    plt.axhline(0.1, color="gray", linestyle="--", linewidth=1.5, label="10% threshold")
    plt.title("MTF by Reconstruction Filter", fontsize=16)
    plt.xlabel("Spatial frequency (cycles/pixel)")
    plt.ylabel("MTF")
    plt.ylim(0, 1.1)
    plt.grid(True, alpha=0.3)
    plt.legend()
    savefig(os.path.join(OUTPUT_DIR, "slide06_filter_mtf.png"))

    plt.figure(figsize=(8, 5))
    for label, (freq, nps_vals) in nps_results.items():
        plt.plot(freq, nps_vals, linewidth=2, label=label)
    plt.title("NPS by Reconstruction Filter", fontsize=16)
    plt.xlabel("Spatial frequency (cycles/pixel)")
    plt.ylabel("NPS")
    plt.yscale("log")
    plt.grid(True, alpha=0.3)
    plt.legend()
    savefig(os.path.join(OUTPUT_DIR, "slide06_filter_nps.png"))


def generate_slide_7_visuals(qa_phantom, metadata):
    dose_levels = [1e6, 1e5, 1e4, 1e3]
    sino, angles = generate_sinogram_fast(qa_phantom, BASE_ANGLES)
    cnr_values = []
    for dose in dose_levels:
        noisy_sino, _ = add_poisson_noise(sino, dose, rng=42)
        recon = reconstruct_fbp(noisy_sino, angles, filter_name="ram-lak")
        cnr, _ = compute_cnr_from_qa_phantom(recon, metadata)
        cnr_values.append(cnr)

    plt.figure(figsize=(8, 5))
    plt.plot(dose_levels, cnr_values, "o-", linewidth=2.5, markersize=8)
    plt.axhline(3.0, color="red", linestyle="--", linewidth=2, label="Rose criterion (CNR = 3)")
    plt.xscale("log")
    plt.gca().invert_xaxis()
    plt.title("CNR vs Dose", fontsize=16)
    plt.xlabel("Incident photons I0")
    plt.ylabel("CNR")
    plt.grid(True, alpha=0.3)
    plt.legend()
    savefig(os.path.join(OUTPUT_DIR, "slide07_cnr_vs_dose.png"))

    projection_counts = [360, 180, 90, 45, 20]
    point_center = metadata["point_insert"]["center_pixel"]
    mtf_results = {}
    recon_results = {}
    rmse_values = []
    ssim_values = []
    for count in projection_counts:
        clean_sino, proj_angles = generate_sinogram_fast(qa_phantom, count)
        # Use clean data here so this plot isolates angular sampling effects.
        recon = reconstruct_fbp(clean_sino, proj_angles, filter_name="ram-lak")
        freq_mtf, mtf_vals = compute_mtf_from_reconstruction(
            recon, method="psf", point_center=point_center, roi_size=48
        )
        mtf_results[count] = (freq_mtf, mtf_vals)
        recon_results[count] = recon
        rmse_values.append(compute_rmse(recon, qa_phantom))
        ssim, _ = compute_ssim(recon, qa_phantom)
        ssim_values.append(ssim)

    fig, axes = plt.subplots(1, len(projection_counts), figsize=(16, 4))
    for ax, count in zip(axes, projection_counts):
        ax.imshow(recon_results[count], cmap="gray", vmin=QA_VMIN, vmax=QA_VMAX)
        ax.set_title(f"{count} projections")
        ax.axis("off")
    fig.suptitle("Angular Sampling: Reconstruction Comparison", fontsize=16)
    savefig(os.path.join(OUTPUT_DIR, "slide07_projection_reconstruction_comparison.png"))

    plt.figure(figsize=(8, 5))
    for count, (freq, mtf) in mtf_results.items():
        plt.plot(freq, mtf, linewidth=2, label=f"{count} projections")
    plt.axhline(0.1, color="gray", linestyle="--", linewidth=1.5, label="10% threshold")
    plt.title("PSF-based MTF vs Number of Projections", fontsize=16)
    plt.xlabel("Spatial frequency (cycles/pixel)")
    plt.ylabel("MTF")
    plt.ylim(0, 1.1)
    plt.grid(True, alpha=0.3)
    plt.legend()
    savefig(os.path.join(OUTPUT_DIR, "slide07_mtf_vs_projections.png"))

    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(projection_counts, rmse_values, "o-", color="tab:red", linewidth=2.5, label="RMSE")
    ax1.set_xlabel("Number of projections")
    ax1.set_ylabel("RMSE", color="tab:red")
    ax1.tick_params(axis="y", labelcolor="tab:red")
    ax1.invert_xaxis()
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(projection_counts, ssim_values, "s-", color="tab:blue", linewidth=2.5, label="SSIM")
    ax2.set_ylabel("SSIM", color="tab:blue")
    ax2.tick_params(axis="y", labelcolor="tab:blue")

    plt.title("Reconstruction Quality vs Number of Projections", fontsize=16)
    savefig(os.path.join(OUTPUT_DIR, "slide07_rmse_ssim_vs_projections.png"))


def write_index():
    index_path = os.path.join(OUTPUT_DIR, "README.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Presentation Visuals\n\n")
        f.write("Generated by `python generate_accurate_presentation_visuals.py`.\n\n")
        f.write("## Files\n\n")
        for filename in sorted(os.listdir(OUTPUT_DIR)):
            if filename.endswith(".png"):
                f.write(f"- `{filename}`\n")
    print(f"Saved {index_path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    qa_phantom, metadata = generate_qa_phantom(SIZE)
    generate_slide_2_visuals(qa_phantom)
    clean_sino, _ = generate_slide_3_visuals(qa_phantom)
    generate_slide_4_visuals(clean_sino)
    generate_slide_5_visuals()
    generate_slide_6_visuals(qa_phantom, metadata)
    generate_slide_7_visuals(qa_phantom, metadata)
    write_index()
    print(f"All accurate presentation visuals saved in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
