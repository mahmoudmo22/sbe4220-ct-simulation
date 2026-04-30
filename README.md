# 2D CT Simulation & System Performance Characterization

**Course:** SBE 4220 — Medical Imaging II | Spring 2026  
**Team 18 Members:** 
- Mahmoud Mohamed
- Mahmoud Bahaa
- Mohamed Ashraf
- Rashed Mamdouh
- Ammar Yasser

---

## 📊 Project Presentation
**[View our final presentation and slides here](https://drive.google.com/drive/folders/17M-3aczupcqZ6xv745jKOBHpaL1YvFRy?usp=drive_link)**

---

## 🔬 Project Overview
This project implements a complete numerical simulation of the 2D X-ray Computed Tomography (CT) pipeline—from physics-based acquisition to image reconstruction—and extends it with a rigorous, quantitative system performance characterization framework based on *Medical Imaging Signals and Systems (Prince & Links)*.

Unlike standard simulations that stop at visual reconstruction, this project quantitatively asks **"how good is the system?"** by measuring:
* **Spatial Resolution:** Modulation Transfer Function (MTF)
* **Noise Texture:** Noise Power Spectrum (NPS)
* **Object Detectability:** Contrast-to-Noise Ratio (CNR)

### The Pipeline
1. **Phantom Generation:** Shepp-Logan phantom and custom QA phantoms.
2. **Forward Projection:** Simulating parallel-beam X-ray acquisition (Beer-Lambert law and Radon transform).
3. **Noise Modeling:** Simulating Poisson noise to model varying radiation dose levels.
4. **Reconstruction:** Filtered Back-Projection (FBP) algorithm.
5. **System Evaluation:** Quantitative assessment using MTF, NPS, CNR, RMSE, and SSIM.

## 📐 Mathematical Foundations
This project is built explicitly on the mathematical theory taught in SBE 4220, rather than relying on black-box external packages.

### 1. Data Acquisition (Physics)
* **Beer-Lambert Law:** Models X-ray attenuation through the object.
  $$I = I_0 e^{-\int \mu(x,y) dl}$$
* **Radon Transform:** The mathematical foundation of parallel-beam forward projection.
  $$p(s, \theta) = \int \int \mu(x,y) \delta(x\cos\theta + y\sin\theta - s) dx dy$$

### 2. Image Reconstruction
* **Filtered Back-Projection (FBP):** Reconstructs the image from projections using the Fourier Slice Theorem.
  $$\mu(x,y) = \int_0^\pi p_{filtered}(\theta, x\cos\theta + y\sin\theta) d\theta$$
  *(Includes custom implementation of the Ramp filter $|w|$ and apodization windows like Hamming).*

### 3. Noise Modeling
* **Poisson Statistics:** Noise is correctly modeled in the *pre-log intensity domain* rather than the sinogram domain, following photon counting physics.
  $$I_{measured} \sim \text{Poisson}(I_{expected})$$

### 4. Quantitative Metrics
* **MTF (Spatial Resolution):** Calculated via the Edge Spread Function.
  $$\text{MTF}(f) = \left| \mathcal{F}\left\{\frac{d}{dx}\text{ESF}(x)\right\} \right|$$
* **CNR (Detectability):** Evaluated against the Rose Criterion ($\text{CNR} \geq 3$).
  $$\text{CNR} = \frac{|\mu_{insert} - \mu_{bg}|}{\sigma_{bg}}$$

## 📂 Repository Structure
* `src/`: Core Python modules for physics simulation, mathematical reconstruction, and evaluation metrics.
* `notebooks/`: Jupyter notebooks containing our experimental pipelines, validations, and visual demonstrations (e.g., parallel beam overlays).
* `documentation/`: Detailed implementation plans, project proposals, and theoretical mappings to the course textbook.
* `results/`: Generated plots, figures, and comparison tables.

## 🚀 How to Run
1. Ensure you have Python 3.10+ installed.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Navigate to the `notebooks/` directory and start Jupyter:
   ```bash
   jupyter notebook
   ```
4. Open any of the experiment notebooks (e.g., `experiment_1_baseline.ipynb`) and run the cells to generate sinograms, perform FBP reconstruction, and visualize the X-ray beam geometry.
