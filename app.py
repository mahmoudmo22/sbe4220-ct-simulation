import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
import sys
import os

# Ensure the src directory is in the path
sys.path.append(os.path.abspath("src"))

from phantom import generate_qa_phantom
from forward_projection import generate_sinogram_fast
from noise_model import add_poisson_noise
from fbp import reconstruct_fbp, AVAILABLE_FILTERS
from mtf import compute_mtf_from_reconstruction
from nps import compute_nps
from cnr import compute_cnr_from_qa_phantom
from metrics import compute_rmse

# -----------------------------------------------------------------------------
# Streamlit App Configuration
# -----------------------------------------------------------------------------
st.set_page_config(page_title="2D CT Simulator", layout="wide", initial_sidebar_state="expanded")

st.title("🖥️ 2D CT Simulation & System Characterization")
st.markdown("**Team 18 | SBE 4220 — Medical Imaging II**")
st.markdown("Use the controls on the left to simulate different scanner parameters and instantly see the effect on the resulting image quality and metrics.")

# -----------------------------------------------------------------------------
# Sidebar Controls
# -----------------------------------------------------------------------------
st.sidebar.header("⚙️ Scanner Parameters")

st.sidebar.markdown("### 1. Radiation Dose")
st.sidebar.markdown("Controls the incident photon count ($I_0$). Lower dose means higher Poisson noise.")
dose_log = st.sidebar.slider("Log10(I₀)", min_value=3.0, max_value=7.0, value=5.0, step=0.5)
I0 = 10**dose_log
st.sidebar.info(f"**Current Dose ($I_0$):** {I0:,.0f} photons")

st.sidebar.markdown("### 2. Angular Sampling")
st.sidebar.markdown("Fewer angles speed up the scan but cause streak artifacts.")
num_angles = st.sidebar.slider("Number of Projections", min_value=10, max_value=360, value=180, step=10)

st.sidebar.markdown("### 3. FBP Reconstruction Filter")
st.sidebar.markdown("Controls the resolution vs. noise tradeoff.")
filter_name = st.sidebar.selectbox("Reconstruction Filter", AVAILABLE_FILTERS, index=0)

st.sidebar.markdown("### 4. Demo Controls")
st.sidebar.markdown("Freeze the noise to make before/after comparisons easier during discussion.")
noise_seed = st.sidebar.number_input("Noise Seed", min_value=0, max_value=9999, value=42, step=1)
show_overlays = st.sidebar.checkbox("Show metric overlays", value=True)

st.sidebar.markdown("### 5. Display Window")
image_vmax = st.sidebar.slider(
    "Image max μ", min_value=0.02, max_value=0.12, value=0.08, step=0.01
)
error_abs_max = st.sidebar.slider(
    "Error map range", min_value=0.005, max_value=0.08, value=0.03, step=0.005
)

# -----------------------------------------------------------------------------
# Data Processing (Cached Phantom Generation)
# -----------------------------------------------------------------------------
@st.cache_data
def get_phantom():
    return generate_qa_phantom(size=256)

def estimate_threshold_frequency(freq, values, threshold=0.1):
    """Return the first interpolated frequency where the curve crosses a threshold."""
    freq = np.asarray(freq)
    values = np.asarray(values)
    finite = np.isfinite(freq) & np.isfinite(values)
    freq = freq[finite]
    values = values[finite]

    below = np.where(values <= threshold)[0]
    if below.size == 0:
        return None

    idx = below[0]
    if idx == 0:
        return freq[0]

    f0, f1 = freq[idx - 1], freq[idx]
    v0, v1 = values[idx - 1], values[idx]
    if v1 == v0:
        return f1
    return f0 + (threshold - v0) * (f1 - f0) / (v1 - v0)

def norm_to_pixel(center_norm, size):
    """Convert normalized (x, y) coordinates to image (row, col)."""
    x_norm, y_norm = center_norm
    col = (x_norm + 1.0) / 2.0 * (size - 1)
    row = (y_norm + 1.0) / 2.0 * (size - 1)
    return row, col

def norm_radius_to_pixels(radius_norm, size):
    """Convert a normalized radius to pixels."""
    return radius_norm / 2.0 * (size - 1)

def add_metric_overlays(ax, metadata, image_size):
    """Draw the QA regions used for MTF, NPS, and CNR."""
    edge = metadata["edge_insert"]
    edge_x = edge["x_range_norm"][1]
    edge_col = (edge_x + 1.0) / 2.0 * (image_size - 1)
    y0 = (edge["y_range_norm"][0] + 1.0) / 2.0 * (image_size - 1)
    y1 = (edge["y_range_norm"][1] + 1.0) / 2.0 * (image_size - 1)
    ax.plot([edge_col, edge_col], [y0, y1], color="cyan", linewidth=2, label="MTF edge")

    insert = metadata["cnr_inserts"][0]
    insert_row, insert_col = norm_to_pixel(insert["center_norm"], image_size)
    insert_radius = norm_radius_to_pixels(insert["radius_norm"] * 0.7, image_size)
    ax.add_patch(Circle(
        (insert_col, insert_row), insert_radius, fill=False,
        edgecolor="lime", linewidth=2, label="CNR insert"
    ))

    uniform = metadata["uniform_roi"]
    bg_row, bg_col = norm_to_pixel(uniform["center_norm"], image_size)
    bg_radius = norm_radius_to_pixels(uniform["radius_norm"] * 0.7, image_size)
    ax.add_patch(Circle(
        (bg_col, bg_row), bg_radius, fill=False,
        edgecolor="yellow", linewidth=2, label="CNR background"
    ))

    roi_size = 32
    ax.add_patch(Rectangle(
        (bg_col - roi_size / 2, bg_row - roi_size / 2), roi_size, roi_size,
        fill=False, edgecolor="magenta", linewidth=2, linestyle="--", label="NPS ROI"
    ))

phantom, metadata = get_phantom()

with st.spinner("Acquiring data and running reconstruction pipeline..."):
    # 1. Forward Projection (Clean Sinogram)
    clean_sino, angles = generate_sinogram_fast(phantom, num_angles)
    
    # 2. Add Poisson Noise (Dose)
    noisy_sino, _ = add_poisson_noise(clean_sino, I0, rng=int(noise_seed))
    
    # 3. Reconstruction (FBP)
    reconstruction = reconstruct_fbp(noisy_sino, angles, filter_name=filter_name)
    error_image = reconstruction - phantom
    
    # 4. Extract Performance Metrics
    # Use the known QA slab edge so MTF is measured from one localized edge.
    edge_x = metadata["edge_insert"]["x_range_norm"][1]
    edge_col = int((edge_x + 1.0) / 2.0 * (reconstruction.shape[1] - 1))
    freq_mtf, mtf_vals = compute_mtf_from_reconstruction(
        reconstruction, method="edge", edge_col=edge_col
    )
    freq_nps, nps_vals, _, _ = compute_nps(reconstruction, roi_size=32, num_rois=8, center=(128, 128))
    cnr, _ = compute_cnr_from_qa_phantom(reconstruction, metadata)
    rmse = compute_rmse(reconstruction, phantom)

# -----------------------------------------------------------------------------
# Main Display Area
# -----------------------------------------------------------------------------
st.divider()

# KPIs
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

# Display CNR with conditional coloring based on Rose Criterion (>= 3.0)
rose_status = "✅ Pass (Rose Criterion)" if cnr >= 3.0 else "❌ Fail (Too Noisy)"
col_kpi1.metric("Contrast-to-Noise Ratio (CNR)", f"{cnr:.2f}", rose_status, delta_color="normal" if cnr >= 3.0 else "inverse")

col_kpi2.metric("Root Mean Square Error (RMSE)", f"{rmse:.4f}")

# Find spatial frequency at 10% MTF as a metric
mtf_10_freq = estimate_threshold_frequency(freq_mtf, mtf_vals, threshold=0.1)
mtf_10_label = f"{mtf_10_freq:.2f} cyc/px" if mtf_10_freq is not None else "Not reached"
col_kpi3.metric("Spatial Resolution (10% MTF)", mtf_10_label)

st.divider()

# Visuals
col_img1, col_img2, col_img3 = st.columns(3)

with col_img1:
    st.subheader("1. Original QA Phantom")
    fig1, ax1 = plt.subplots(figsize=(6, 5))
    im1 = ax1.imshow(phantom, cmap="gray", vmin=0, vmax=image_vmax)
    plt.colorbar(im1, ax=ax1, label="Attenuation μ(x,y)")
    if show_overlays:
        add_metric_overlays(ax1, metadata, phantom.shape[0])
        ax1.legend(loc="lower right", fontsize=7)
    ax1.axis("off")
    st.pyplot(fig1)

with col_img2:
    st.subheader("2. Reconstructed Image")
    fig2, ax2 = plt.subplots(figsize=(6, 5))
    im2 = ax2.imshow(reconstruction, cmap="gray", vmin=0, vmax=image_vmax)
    plt.colorbar(im2, ax=ax2, label="Attenuation μ(x,y)")
    if show_overlays:
        add_metric_overlays(ax2, metadata, reconstruction.shape[0])
        ax2.legend(loc="lower right", fontsize=7)
    ax2.axis("off")
    st.pyplot(fig2)

with col_img3:
    st.subheader("3. Reconstruction Error")
    fig_err, ax_err = plt.subplots(figsize=(6, 5))
    im_err = ax_err.imshow(
        error_image, cmap="seismic", vmin=-error_abs_max, vmax=error_abs_max
    )
    plt.colorbar(im_err, ax=ax_err, label="Reconstruction - Phantom")
    ax_err.axis("off")
    st.pyplot(fig_err)

st.divider()

col_sino1, col_sino2 = st.columns(2)

with col_sino1:
    st.subheader("4. Clean Sinogram")
    fig_clean, ax_clean = plt.subplots(figsize=(6, 4))
    im_clean = ax_clean.imshow(clean_sino, cmap="hot", aspect="auto")
    plt.colorbar(im_clean, ax=ax_clean, label="Line Integral Value")
    ax_clean.set_xlabel("Projection Angle Index")
    ax_clean.set_ylabel("Detector Bin")
    st.pyplot(fig_clean)

with col_sino2:
    st.subheader("5. Noisy Sinogram")
    fig_noisy, ax_noisy = plt.subplots(figsize=(6, 4))
    im_noisy = ax_noisy.imshow(noisy_sino, cmap="hot", aspect="auto")
    plt.colorbar(im_noisy, ax=ax_noisy, label="Line Integral Value")
    ax_noisy.set_xlabel("Projection Angle Index")
    ax_noisy.set_ylabel("Detector Bin")
    st.pyplot(fig_noisy)

st.divider()

# Quantitative Graphs
col_plot1, col_plot2 = st.columns(2)

with col_plot1:
    st.subheader("Spatial Resolution (MTF)")
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    ax3.plot(freq_mtf, mtf_vals, linewidth=2, color="blue", label="MTF")
    ax3.axhline(0.1, color='gray', linestyle='--', label="10% Threshold")
    ax3.set_xlabel("Spatial Frequency (cycles/pixel)")
    ax3.set_ylabel("Modulation Transfer Function")
    ax3.set_ylim(0, 1.1)
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    st.pyplot(fig3)

with col_plot2:
    st.subheader("Noise Texture (NPS)")
    fig4, ax4 = plt.subplots(figsize=(6, 4))
    ax4.plot(freq_nps, nps_vals, linewidth=2, color="red", label="NPS")
    ax4.set_xlabel("Spatial Frequency (cycles/pixel)")
    ax4.set_ylabel("Noise Power Spectrum (Log Scale)")
    ax4.set_yscale("log")
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    st.pyplot(fig4)
