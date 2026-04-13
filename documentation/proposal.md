# Full Project Proposal — Team 18

**Course:** SBE 4220 — Medical Imaging II | Spring 2026
**Submission Date:** April 13, 2026

---

## Team Members

| #  | Name              |
|----|-------------------|
| 1  | Mahmoud Mohamed   |
| 2  | Mahmoud Bahaa     |
| 3  | Mohamed Ashraf    |
| 4  | Rashed Mamdouh   |
| 5  | Ammar Yasser      |

---

## Project Title

**Numerical Simulation and Performance Characterization of a 2D CT System: Acquisition, Reconstruction, and Quantitative Image Quality Assessment (MTF, NPS, CNR)**

---

## 1. Project Description

This project implements a complete numerical simulation of the 2D X-ray Computed Tomography (CT) pipeline — from physics-based acquisition to image reconstruction — and extends it with a rigorous, quantitative system performance characterization framework.

We simulate the forward projection process using the Beer-Lambert attenuation model, generate sinograms under parallel-beam geometry, add realistic Poisson noise to model varying dose levels, and reconstruct images using Filtered Back Projection (FBP) with multiple filter kernels.

The distinguishing contribution of this project is the quantitative evaluation of CT system performance using established metrics from medical physics:

- **Modulation Transfer Function (MTF)** — to measure spatial resolution
- **Noise Power Spectrum (NPS)** — to characterize noise texture and frequency content
- **Contrast-to-Noise Ratio (CNR)** — to assess object detectability

We systematically study how acquisition parameters (number of projections, dose level) and reconstruction parameters (filter choice) affect these performance metrics, providing a systems-level understanding of CT image quality trade-offs.

### What Makes This Project Unique

Most CT simulation projects stop at "reconstruct and show it looks good." This project goes further by asking **"how good is it, quantitatively?"** — measuring spatial resolution (MTF), noise characteristics (NPS), and object detectability (CNR) under varying conditions. This is how real CT systems are evaluated in clinical medical physics.

---

## 2. Imaging Modality

**X-ray Computed Tomography (CT)** — 2D parallel-beam geometry.

---

## 3. Simulation Pipeline

```
Phantom Generation → Forward Projection (Sinogram) → Noise Addition → Reconstruction (FBP) → Performance Evaluation (MTF, NPS, CNR)
```

### 3.1 Phantom Generation

- **Shepp-Logan phantom**: standard analytical phantom composed of parameterized ellipses with known attenuation coefficients, used for visual reconstruction quality assessment.
- **Custom QA phantom**: designed specifically for quantitative metrics evaluation, containing:
  - A small high-contrast point/wire insert for PSF/MTF measurement.
  - A sharp edge for Edge Spread Function (ESF)-based MTF measurement.
  - Low-contrast inserts at known μ values for CNR measurement.
  - A uniform region for NPS measurement.

### 3.2 Forward Projection (Sinogram Generation)

- Parallel-beam ray-tracing through the phantom to compute line integrals of the attenuation coefficient μ(x, y) based on **Beer-Lambert's Law**:

```
I = I₀ · exp(−∫ μ(x,y) dl)
p = −ln(I / I₀) = ∫ μ(x,y) dl
```

- Sinograms are generated for varying numbers of projection angles (e.g., 360, 180, 90, 45, 20, 10) to study the effect of angular sampling on reconstruction quality.

### 3.3 Noise Modeling

- Realistic **Poisson noise** applied in the pre-log intensity domain (since photon counting follows a Poisson distribution):

```
I_measured ~ Poisson(I₀ · exp(−∫ μ dl))
```

- Multiple dose levels simulated by varying the incident photon count I₀: 10⁶, 10⁵, 10⁴, 10³.
- Noise propagation through the log-transform and into the reconstruction domain is studied.

### 3.4 Filtered Back Projection (FBP) Reconstruction

- Custom implementation of FBP based on the **Fourier Slice Theorem**.
- **Step 1 — Filtering:** each projection is filtered in the frequency domain:

```
p_filtered(θ, s) = F⁻¹{ |ω| · H(ω) · F{p(θ, s)} }
```

  where H(ω) is the apodization window.

- **Step 2 — Back Projection:** filtered projections are smeared back across the image grid and summed over all angles.
- Multiple filter kernels implemented: **Ram-Lak** (ramp), **Shepp-Logan**, **Cosine**, and **Hamming**-windowed ramp.

### 3.5 System Performance Metrics

#### MTF (Modulation Transfer Function)
Measures the system's ability to preserve contrast at each spatial frequency.

- **PSF method:** reconstruct a point object → compute |FFT(PSF)|, normalized.
- **Edge method:** reconstruct a sharp edge → extract ESF → differentiate to get LSF → compute |FFT(LSF)|, normalized.

#### NPS (Noise Power Spectrum)
Characterizes the frequency distribution of noise in reconstructed images.

- Extract uniform ROIs from noisy reconstructions.
- Compute 2D NPS = ⟨|FFT(ROI − mean)|²⟩ averaged over multiple ROIs.
- Radially average to obtain 1D NPS(f).

#### CNR (Contrast-to-Noise Ratio)
Quantifies object detectability against a noisy background.

```
CNR = |μ_insert − μ_background| / σ_background
```

Evaluated against the Rose criterion (CNR ≥ 3–5 for reliable human detection).

---

## 4. Experiments

| # | Experiment | Description |
|---|-----------|-------------|
| 1 | **Baseline Reconstruction Quality** | Reconstruct Shepp-Logan phantom at 360, 180, 90, 45, 20, 10 projection angles. Visual comparison + RMSE/SSIM. Demonstrate streak artifacts at low angle counts. |
| 2 | **Filter Comparison** | Reconstruct the same noisy sinogram with Ram-Lak, Shepp-Logan, Cosine, and Hamming filters. Measure MTF and NPS for each to quantify the resolution-noise trade-off. |
| 3 | **Dose vs. Image Quality** | Fix 180 projections, vary I₀ from 10⁶ to 10³. Measure NPS, CNR, RMSE, and SSIM at each dose. Plot all metrics vs. dose. |
| 4 | **MTF vs. Number of Projections** | Fix dose (I₀ = 10⁵), vary projections. Measure MTF degradation with angular undersampling. |
| 5 | **Integrated System Characterization** | Select representative operating points (high/low dose × many/few angles). Show side-by-side: reconstruction, MTF curve, NPS curve, CNR value. Summary comparison table. |
| 6 | **Detectability Index (Bonus)** | Compute NEQ(f) = MTF²(f) / NPS(f) to unify resolution and noise into a single efficiency metric. |

---

## 5. Task Division

### Mahmoud Mohamed — Phantom Generation & Forward Projection

- Implement the Shepp-Logan phantom generator (parameterized ellipses).
- Design and implement the custom QA phantom for MTF/NPS/CNR measurement.
- Implement the parallel-beam forward projector (ray-tracing + Beer-Lambert).
- Generate sinograms for multiple projection angle configurations.

### Mahmoud Bahaa — FBP Reconstruction & Filter Analysis

- Implement Filtered Back Projection from scratch.
- Implement multiple filter kernels: Ram-Lak, Shepp-Logan, Cosine, Hamming.
- Reconstruct images from sinograms and deliver to other members for analysis.
- Analyze and visualize the effect of each filter on reconstruction quality.

### Mohamed Ashraf — Noise Modeling & Dose Simulation

- Implement the Poisson noise model on raw projection data (pre-log domain).
- Simulate multiple dose levels by varying I₀.
- Generate dose-vs-quality curves (SNR, RMSE, SSIM as functions of I₀).
- Study and visualize noise propagation through the reconstruction pipeline.

### Rashed Mamdouh — System Performance Metrics (MTF, NPS, CNR)

- Implement MTF measurement using both PSF and edge methods.
- Implement NPS computation (2D FFT, ROI averaging, radial averaging to 1D).
- Implement CNR measurement from ROI-based statistics.
- Lead the integrated analysis combining all three metrics.

### Ammar Yasser — Experiments, Analysis & Presentation

- Design and execute all systematic experiments (parameter sweeps).
- Compute basic image quality metrics (RMSE, SSIM, SNR) across experiments.
- Produce all comparison plots, summary tables, and publication-quality figures.
- Lead presentation slide preparation and final integration.

### Shared Responsibilities (All Members)

- Every member must understand the full pipeline end-to-end.
- Every member must be able to explain MTF, NPS, and CNR conceptually.
- Code review: each member reviews at least one other member's module.
- Each member prepares individually for the professor's Q&A.

---

## 6. Tools & Technologies

| Tool / Library | Purpose |
|----------------|---------|
| **Python 3.10+** | Primary programming language |
| **NumPy** | Array operations, FFT, linear algebra |
| **SciPy** | Interpolation, signal processing utilities |
| **Matplotlib** | Visualization, plotting, publication-quality figures |
| **scikit-image** | Reference validation only (e.g., `skimage.transform.radon`) |
| **Jupyter Notebook** | Interactive experiment notebooks |
| **Git / GitHub** | Version control and collaboration |

> **Note:** Core algorithms (forward projection, FBP, MTF/NPS/CNR computation) are implemented from scratch to demonstrate understanding. Library functions are used for validation only.

---

## 7. Code Structure

```
imaging_project/
├── documentation/
│   ├── requrments.md
│   ├── project_description.md
│   ├── implementation_plan.md
│   └── proposal.md
├── src/
│   ├── phantom.py              # Shepp-Logan + QA phantom generation
│   ├── forward_projection.py   # Ray-tracing, sinogram generation
│   ├── noise_model.py          # Poisson noise, dose simulation
│   ├── fbp.py                  # Filtered Back Projection + filters
│   ├── mtf.py                  # MTF measurement (PSF + edge method)
│   ├── nps.py                  # NPS computation (2D → radial → 1D)
│   ├── cnr.py                  # CNR measurement from ROIs
│   ├── metrics.py              # Basic metrics (RMSE, SSIM, SNR)
│   └── utils.py                # Shared utilities (display, I/O, ROI extraction)
├── notebooks/
│   ├── experiment_1_baseline.ipynb
│   ├── experiment_2_filters.ipynb
│   ├── experiment_3_dose.ipynb
│   ├── experiment_4_mtf_projections.ipynb
│   ├── experiment_5_system_characterization.ipynb
│   └── experiment_6_detectability.ipynb  (bonus)
├── results/                    # Saved figures and tables
├── presentation/               # Slides
└── README.md
```

---

## 8. Timeline & Deliverables

| Week | Dates | Milestone | Deliverable |
|------|-------|-----------|-------------|
| 1 | Apr 6 – Apr 12 | Short description submitted. Repo setup. Theory study. | Project description |
| 2 | Apr 13 – Apr 19 | Full proposal submitted. Phantom + Forward Projector complete. Basic FBP working. | This proposal |
| 3 | Apr 20 – Apr 26 | Noise model complete. MTF/NPS/CNR modules working. All experiments running. | Working codebase |
| 4 | Apr 27 – Apr 30 | Final integration, presentation slides, code cleanup. | All code + slides submitted |
| Presentation | May 4 | Individual Q&A with professor. | Oral presentation & discussion |

---

## 9. Expected Outcomes

1. A fully functional 2D CT simulator covering acquisition, noise modeling, and reconstruction.
2. Quantitative characterization of system performance using MTF, NPS, and CNR — the standard metrics used in clinical CT quality assurance.
3. Systematic analysis of how projection count, dose level, and filter choice affect image quality, demonstrated through parameter sweep experiments.
4. Publication-quality figures and comparison tables summarizing trade-offs.
5. (Bonus) Noise-Equivalent Quanta NEQ(f) = MTF²(f) / NPS(f) as a unified system efficiency metric.

---

## 10. References

- Prince, J. L., & Links, J. M. *Medical Imaging: Signals and Systems* (2nd ed.) — Chapters 6–7.
- Bushberg, J. T., et al. *The Essential Physics of Medical Imaging* — Chapter 10.
- AAPM Report 233 — CT Image Quality Metrics and Performance Evaluation.
- ICRU Report 87 — Radiation Dose and Image Quality for CT.
