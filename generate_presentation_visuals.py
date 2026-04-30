import numpy as np
import matplotlib.pyplot as plt
import os
import sys

# Ensure src modules can be imported
sys.path.append(os.path.abspath("src"))

from phantom import generate_shepp_logan, generate_qa_phantom, norm_to_pixel
from forward_projection import generate_sinogram
from noise_model import add_poisson_noise
from fbp import reconstruct_fbp

# Ensure results directory exists
os.makedirs("results", exist_ok=True)

# Common params
size = 256
num_angles = 180

print("Generating presentation visuals...")

# ---------------------------------------------------------
# Slide 2: Data Acquisition & Physics
# ---------------------------------------------------------
print("Generating Shepp-Logan and Parallel Beams...")
shepp = generate_shepp_logan(size)
plt.figure(figsize=(6, 6))
plt.imshow(shepp, cmap='gray', vmin=0, vmax=0.05)
plt.axis('off')
plt.title("2D Shepp-Logan Phantom", fontsize=16)
plt.tight_layout()
plt.savefig("results/pres_shepp_logan.png", dpi=300, bbox_inches='tight', transparent=True)
plt.close()

# Parallel beams overlay (2x2 grid)
from matplotlib.transforms import Affine2D

fig, axes = plt.subplots(2, 2, figsize=(10, 10), facecolor='black')
angles = [0, 45, 90, 135]

for i, ax in enumerate(axes.flatten()):
    angle = angles[i]
    ax.imshow(shepp, cmap='gray', vmin=0, vmax=0.05)
    
    # Create a rotation transform around the center of the image
    transform = Affine2D().rotate_deg_around(size/2, size/2, -angle) + ax.transData
    
    # Draw parallel red lines to simulate X-ray beams
    # Standard Radon convention: 0 degrees = integrating along y-axis (vertical rays)
    x_vals = np.linspace(20, size-20, 20)
    for x in x_vals:
        ax.plot([x, x], [0, size], color='red', alpha=0.5, linewidth=1.5, transform=transform)
        
    ax.axis('off')
    ax.set_title(f"{angle}° Projection", color='white', fontsize=16)

plt.tight_layout()
plt.savefig("results/pres_parallel_beams_grid.png", dpi=300, bbox_inches='tight', facecolor='black')
plt.close()

# ---------------------------------------------------------
# Slide 3: Filtered Back-Projection
# ---------------------------------------------------------
print("Generating Clean Sinogram and Reconstruction...")
clean_sino, angles = generate_sinogram(shepp, num_angles)

plt.figure(figsize=(6, 6))
plt.imshow(clean_sino, cmap='hot', aspect='auto')
plt.xlabel("Projection Angle Index", fontsize=12)
plt.ylabel("Detector Bin", fontsize=12)
plt.title("Clean Sinogram (Radon Transform)", fontsize=16)
plt.tight_layout()
plt.savefig("results/pres_clean_sinogram.png", dpi=300, bbox_inches='tight')
plt.close()

recon = reconstruct_fbp(clean_sino, angles, filter_name='ram-lak')
plt.figure(figsize=(6, 6))
plt.imshow(recon, cmap='gray', vmin=0, vmax=0.05)
plt.axis('off')
plt.title("FBP Reconstruction (Ram-Lak)", fontsize=16)
plt.tight_layout()
plt.savefig("results/pres_reconstruction.png", dpi=300, bbox_inches='tight', transparent=True)
plt.close()

# ---------------------------------------------------------
# Slide 4: Noise & Dose Modeling
# ---------------------------------------------------------
print("Generating High and Low Dose Sinograms...")
high_dose_I0 = 1e6
low_dose_I0 = 1e3  # Lower dose to make the visual difference very obvious

sino_high, _ = add_poisson_noise(clean_sino, high_dose_I0)
sino_low, _ = add_poisson_noise(clean_sino, low_dose_I0)

plt.figure(figsize=(6, 6))
plt.imshow(sino_high, cmap='hot', aspect='auto')
plt.title(f"High Dose Sinogram ($I_0 = 10^6$)", fontsize=16)
plt.xlabel("Angle Index", fontsize=12)
plt.ylabel("Detector Bin", fontsize=12)
plt.tight_layout()
plt.savefig("results/pres_high_dose_sino.png", dpi=300, bbox_inches='tight')
plt.close()

plt.figure(figsize=(6, 6))
plt.imshow(sino_low, cmap='hot', aspect='auto')
plt.title(f"Low Dose Sinogram ($I_0 = 10^3$)", fontsize=16)
plt.xlabel("Angle Index", fontsize=12)
plt.ylabel("Detector Bin", fontsize=12)
plt.tight_layout()
plt.savefig("results/pres_low_dose_sino.png", dpi=300, bbox_inches='tight')
plt.close()

# ---------------------------------------------------------
# Slide 5: QA Phantom (Metrics)
# ---------------------------------------------------------
print("Generating QA Phantom...")
qa_phantom, metadata = generate_qa_phantom(size)
plt.figure(figsize=(6, 6))
plt.imshow(qa_phantom, cmap='gray', vmin=0, vmax=0.05)

# Annotate Edge for MTF
edge_pixel = norm_to_pixel((-0.30, 0.0), size)
plt.annotate("MTF Edge", xy=(edge_pixel[1], edge_pixel[0]), xytext=(edge_pixel[1] + 60, edge_pixel[0] - 60),
             arrowprops=dict(facecolor='blue', shrink=0.05), color='blue', fontsize=14, ha='center', weight='bold')

# Annotate Circles for CNR
cnr_inserts = metadata['cnr_inserts']
if len(cnr_inserts) > 0:
    center_tumor = norm_to_pixel(cnr_inserts[0]['center_norm'], size)
    plt.annotate("CNR Targets", xy=(center_tumor[1], center_tumor[0]), xytext=(size-40, size-40),
                 arrowprops=dict(facecolor='red', shrink=0.05), color='red', fontsize=14, ha='center', weight='bold')

plt.axis('off')
plt.title("QA Phantom (Targets)", fontsize=16)
plt.tight_layout()
plt.savefig("results/pres_qa_phantom.png", dpi=300, bbox_inches='tight', transparent=True)
plt.close()

print("All presentation visuals generated successfully in 'results/' directory!")
