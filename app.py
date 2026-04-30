import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Ensure the src directory is in the path
sys.path.append(os.path.abspath("src"))

from phantom import generate_qa_phantom
from forward_projection import generate_sinogram
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

# -----------------------------------------------------------------------------
# Data Processing (Cached Phantom Generation)
# -----------------------------------------------------------------------------
@st.cache_data
def get_phantom():
    return generate_qa_phantom(size=256)

phantom, metadata = get_phantom()

with st.spinner("Acquiring data and running reconstruction pipeline..."):
    # 1. Forward Projection (Clean Sinogram)
    clean_sino, angles = generate_sinogram(phantom, num_angles)
    
    # 2. Add Poisson Noise (Dose)
    noisy_sino, _ = add_poisson_noise(clean_sino, I0)
    
    # 3. Reconstruction (FBP)
    reconstruction = reconstruct_fbp(noisy_sino, angles, filter_name=filter_name)
    
    # 4. Extract Performance Metrics
    freq_mtf, mtf_vals = compute_mtf_from_reconstruction(reconstruction, method="edge")
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
mtf_10_idx = np.argmin(np.abs(mtf_vals - 0.1))
col_kpi3.metric("Spatial Resolution (10% MTF)", f"{freq_mtf[mtf_10_idx]:.2f} cyc/px")

st.divider()

# Visuals
col_img1, col_img2 = st.columns(2)

with col_img1:
    st.subheader("1. Noisy Sinogram (Raw Data)")
    fig1, ax1 = plt.subplots(figsize=(6, 5))
    im1 = ax1.imshow(noisy_sino, cmap="hot", aspect="auto")
    plt.colorbar(im1, ax=ax1, label="Line Integral Value")
    ax1.set_xlabel("Projection Angle Index")
    ax1.set_ylabel("Detector Bin")
    st.pyplot(fig1)

with col_img2:
    st.subheader("2. Reconstructed Image")
    fig2, ax2 = plt.subplots(figsize=(6, 5))
    im2 = ax2.imshow(reconstruction, cmap="gray", vmin=0, vmax=0.05)
    plt.colorbar(im2, ax=ax2, label="Attenuation μ(x,y)")
    ax2.axis('off')
    st.pyplot(fig2)

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
