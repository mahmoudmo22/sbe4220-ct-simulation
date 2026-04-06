# Implementation Plan — 2D CT Simulation Project

## Team: 4 Members | Course: SBE 4220 — Medical Imaging II | Spring 2026

---

## 1. Project Overview

Build a Python-based 2D CT simulator that covers the full pipeline:

```
Phantom → Forward Projection (Sinogram) → Add Noise → Reconstruction → Analysis
```

### Modules

| Module | Description |
|--------|-------------|
| **Phantom Generator** | Create/load digital test objects (Shepp-Logan, custom shapes) |
| **Forward Projector** | Simulate X-ray acquisition using ray-tracing + Beer-Lambert law |
| **Noise Model** | Add realistic Poisson noise to simulate different dose levels |
| **Reconstruction (FBP)** | Filtered Back Projection with multiple filter options |
| **Reconstruction (Iterative)** | Algebraic Reconstruction Technique (ART/SART) |
| **Analysis & Visualization** | Metrics (RMSE, SSIM, SNR), artifact visualization, comparison plots |

---

## 2. Timeline

| Week | Dates | Milestone |
|------|-------|-----------|
| **Week 1** | Apr 6 – Apr 12 | Submit short description. All members study core theory. Set up repo, agree on code structure. |
| **Week 2** | Apr 13 – Apr 19 | Submit full proposal. Phantom + Forward Projector complete. Basic FBP working. |
| **Week 3** | Apr 20 – Apr 26 | Noise model, iterative reconstruction, all experiments running. |
| **Week 4** | Apr 27 – Apr 30 | Final integration, presentation slides, code cleanup. Submit by Apr 30. |
| **Presentation** | May 4 | Individual Q&A with professor. |

---

## 3. Task Division (4 Members)

### Member A — Phantom & Forward Projection

**Responsibilities:**
- Implement the Shepp-Logan phantom generator (parameterized ellipses)
- Implement the forward projector: parallel-beam ray-tracing
- Generate sinograms for different numbers of projection angles (e.g., 180, 90, 45, 20)
- (Optional) Extend to fan-beam geometry

**Must understand:**
- Beer-Lambert law and how line integrals of μ(x,y) produce projection values
- How the sinogram is structured (rows = detector bins, columns = angles)
- The geometry of parallel-beam vs. fan-beam

---

### Member B — FBP Reconstruction & Filters

**Responsibilities:**
- Implement Filtered Back Projection from scratch (not just calling a library)
- Implement multiple filters: Ram-Lak (ramp), Shepp-Logan, cosine, Hamming-windowed ramp
- Reconstruct from sinograms produced by Member A
- Visualize the effect of each filter on reconstruction quality

**Must understand:**
- The Fourier Slice Theorem (the theoretical foundation of FBP)
- Why filtering is necessary (the 1/r blurring problem in naive back projection)
- The frequency-domain interpretation of each filter
- How to implement the filter-then-backproject pipeline

---

### Member C — Noise Modeling & Dose Trade-offs

**Responsibilities:**
- Implement Poisson noise model on raw projection data (pre-log)
- Simulate different dose levels by varying I₀ (incident photon count)
- Reconstruct noisy sinograms and measure image quality (SNR, RMSE, SSIM)
- Generate dose-vs-quality curves
- (Optional) Implement a simple post-reconstruction denoising (e.g., Gaussian smoothing) and show its effect

**Must understand:**
- Poisson statistics: why photon counting follows Poisson distribution
- The relationship between dose (I₀), noise variance, and image SNR
- How noise propagates through the log transform and into reconstruction
- ALARA principle (clinical motivation)

---

### Member D — Iterative Reconstruction (ART) & Final Analysis

**Responsibilities:**
- Implement ART (Algebraic Reconstruction Technique) or SART
- Compare ART vs. FBP under sparse-view conditions (few projection angles)
- Generate the system matrix for small phantoms (or use ray-driven on-the-fly computation)
- Lead the final comparison: create summary plots and tables
- Co-lead presentation slide preparation

**Must understand:**
- How ART formulates reconstruction as solving Ax = b
- The iterative update rule and relaxation parameter
- Why iterative methods handle sparse data better than FBP
- Convergence behavior and computational cost trade-off

---

## 4. Shared Responsibilities (All Members)

- **Everyone** must understand the full pipeline and be able to explain any part
- **Everyone** prepares for the professor's Q&A individually
- Code reviews: each member reviews at least one other member's module
- Presentation: each member presents their module (~5 min each)

---

## 5. Suggested Tools & Libraries

| Tool | Purpose |
|------|---------|
| **Python 3.10+** | Primary language |
| **NumPy** | Array operations, FFT, linear algebra |
| **Matplotlib** | Visualization and plotting |
| **scikit-image** | Reference implementations for validation (e.g., `skimage.transform.radon`) — use ONLY for validation, not as your main implementation |
| **SciPy** | Sparse matrices (for ART system matrix), interpolation |
| **CTLab** (optional) | Reference simulator to validate your results against |

**Important:** The core algorithms (forward projection, FBP, ART) should be implemented from scratch to demonstrate understanding. Library functions can be used for validation.

---

## 6. Experiments to Run

### Experiment 1: Effect of Number of Projections
- Reconstruct the Shepp-Logan phantom using FBP with 180, 90, 45, 20, and 10 projection angles
- Measure RMSE and SSIM for each
- Show streak artifacts appearing as angles decrease

### Experiment 2: Filter Comparison
- Reconstruct the same sinogram using Ram-Lak, Shepp-Logan, cosine, and Hamming filters
- Show the noise-resolution trade-off (sharper filters amplify noise)

### Experiment 3: Dose vs. Quality
- Fix 180 projections, vary I₀ from 10⁶ down to 10² photons
- Show noise increasing in reconstructions
- Plot SNR and SSIM vs. dose

### Experiment 4: FBP vs. ART under Sparse Views
- Use 20 and 10 projection angles
- Compare FBP (streaks) vs. ART (smoother, fewer artifacts)
- Show convergence of ART over iterations

### Experiment 5 (Bonus): Beam Hardening Artifact
- Simulate polychromatic X-ray spectrum (2-3 energy bins)
- Show cupping artifact in reconstruction of a uniform cylinder
- Demonstrate a simple linearization correction

---

## 7. Code Structure

```
imaging_project/
├── documentation/
│   ├── requrments.md
│   ├── project_description.md
│   └── implementation_plan.md
├── src/
│   ├── phantom.py              # Shepp-Logan and custom phantom generation
│   ├── forward_projection.py   # Ray-tracing, sinogram generation
│   ├── noise_model.py          # Poisson noise, dose simulation
│   ├── fbp.py                  # Filtered Back Projection + filters
│   ├── art.py                  # Algebraic Reconstruction Technique
│   ├── metrics.py              # RMSE, SSIM, SNR computation
│   └── utils.py                # Shared utilities (display, I/O)
├── notebooks/
│   ├── experiment_1_projections.ipynb
│   ├── experiment_2_filters.ipynb
│   ├── experiment_3_dose.ipynb
│   ├── experiment_4_fbp_vs_art.ipynb
│   └── experiment_5_beam_hardening.ipynb  (bonus)
├── results/                    # Saved figures and tables
├── presentation/               # Slides
└── README.md
```

---

## 8. What to Study for the Professor's Discussion

This is the most critical section. The professor will grill each member individually. Below is everything you need to understand, organized from foundational to advanced.

---

### 8.1 Physics of X-ray CT

#### Beer-Lambert Law (everyone must know cold)
```
I = I₀ · exp(−∫ μ(x,y) dl)
```
- **I₀**: incident photon intensity (number of photons emitted by the X-ray tube)
- **I**: measured intensity at the detector after passing through the object
- **μ(x,y)**: linear attenuation coefficient at position (x,y) — this is what we want to reconstruct
- **∫dl**: line integral along the ray path from source to detector
- The measured quantity is the line integral: `p = −ln(I/I₀) = ∫ μ(x,y) dl`

**Be ready to answer:**
- "What physical quantity does each pixel in a CT image represent?" → The linear attenuation coefficient μ
- "What assumptions does Beer-Lambert make?" → Monochromatic beam, no scatter, narrow beam geometry
- "What happens when these assumptions are violated?" → Beam hardening (polychromatic), scatter artifacts

#### X-ray Interaction with Matter
- **Photoelectric absorption**: dominates at low energies, depends on Z³/E³
- **Compton scattering**: dominates at diagnostic energies (30-150 keV), depends on electron density
- You don't need to derive cross-sections, but know that μ depends on photon energy and tissue composition

#### Hounsfield Units (contextual knowledge)
```
HU = 1000 × (μ - μ_water) / μ_water
```
- Water = 0 HU, air = -1000 HU, bone ≈ +1000 HU
- Not central to simulation but the professor might ask

---

### 8.2 Mathematics of CT Reconstruction

#### The Radon Transform (core concept)
```
p(θ, s) = ∫∫ μ(x,y) · δ(x·cosθ + y·sinθ − s) dx dy
```
- This is the mathematical model of a projection: integrate μ along a line defined by angle θ and offset s
- The collection of all projections p(θ, s) for all angles is the **sinogram**
- Named because a point object traces a sinusoidal curve in (θ, s) space

**Be ready to answer:**
- "What is a sinogram?" → It's the Radon transform of the object. Each column is a projection at one angle. Each row tracks a particular detector position across all angles.
- "Why is it called a sinogram?" → A point at (x₀, y₀) appears as a sinusoidal curve: s = x₀·cosθ + y₀·sinθ

#### The Fourier Slice Theorem (most important theorem)
```
F₁D{p(θ, s)}(ω) = F₂D{μ(x,y)}(ω·cosθ, ω·sinθ)
```
- The 1D Fourier transform of a projection at angle θ gives a line (slice) through the 2D Fourier transform of the object, at the same angle θ
- This means: if you collect projections at enough angles, you fill up the entire 2D Fourier space → you can reconstruct μ(x,y) by inverse 2D FFT

**Be ready to answer:**
- "How does the Fourier Slice Theorem connect projections to reconstruction?" → Each projection gives one line in 2D Fourier space. With enough angles, we can fill 2D Fourier space and invert.
- "What happens with too few angles?" → Fourier space is undersampled, leading to streak artifacts (missing information between the measured slices).

#### Filtered Back Projection (the main reconstruction algorithm)

**Step 1 — Filter each projection:**
```
p_filtered(θ, s) = F⁻¹{ |ω| · F{p(θ, s)} }
```
The |ω| filter (Ram-Lak / ramp filter) compensates for the non-uniform sampling density in Fourier space (more samples near the origin, fewer at high frequencies).

**Step 2 — Back-project:**
```
μ(x,y) = ∫₀^π p_filtered(θ, x·cosθ + y·sinθ) dθ
```
For each pixel (x,y), sum the filtered projection values from all angles.

**Be ready to answer:**
- "Why can't you just back-project without filtering?" → Naive back projection produces a blurred image (convolved with 1/r). The ramp filter corrects this by boosting high frequencies.
- "What does the ramp filter do in the frequency domain?" → It weights frequency components by |ω|, compensating for the fact that low frequencies are overrepresented in the back projection.
- "What is the trade-off with the ramp filter?" → It amplifies high-frequency noise. Windowed filters (Hamming, Shepp-Logan) reduce noise at the cost of spatial resolution.

---

### 8.3 Noise and Dose

#### Poisson Noise Model
```
I_measured ~ Poisson(I₀ · exp(−∫μ dl))
```
- Photon counting is a Poisson process: variance = mean
- Lower dose (fewer photons I₀) → higher relative noise
- After the log transform: `p = −ln(I_measured/I₀)`, the noise is approximately Gaussian with variance ≈ 1/I_measured

**Be ready to answer:**
- "How does dose relate to noise?" → Dose ∝ I₀. Noise standard deviation ∝ 1/√I₀. So halving the dose increases noise by √2.
- "Where in the pipeline do you add noise?" → To the raw intensity I (before the log transform), because photon counting is Poisson in the intensity domain, not in the projection domain.

---

### 8.4 Iterative Reconstruction (ART)

#### Algebraic Formulation
```
Ax = b
```
- **x**: the image (flattened to a vector, N² × 1)
- **b**: the sinogram (flattened, M × 1)
- **A**: the system matrix (M × N²), where A_ij = length of ray i through pixel j

#### ART Update Rule
```
x^(k+1) = x^(k) + λ · (bᵢ − aᵢ·x^(k)) / (aᵢ·aᵢ) · aᵢᵀ
```
- Iterate over rays i = 1, 2, ..., M
- λ is the relaxation parameter (typically 0.1 to 1.0)
- Each update corrects the image so that the projection along ray i matches the measured value

**Be ready to answer:**
- "What is the advantage of iterative methods over FBP?" → They can incorporate prior knowledge (positivity, smoothness), handle noise better, and work with incomplete data (few angles).
- "What is the disadvantage?" → Much slower (many iterations, each requiring forward and back projection). The system matrix can be very large.
- "What does the relaxation parameter λ control?" → Step size. Too large → oscillation/divergence. Too small → slow convergence.

---

### 8.5 Artifacts (know causes and appearance)

| Artifact | Cause | Appearance |
|----------|-------|------------|
| **Streak artifacts** | Too few projection angles (angular undersampling) | Bright/dark lines radiating from high-contrast edges |
| **Ring artifacts** | Miscalibrated detector elements | Concentric rings centered on rotation axis |
| **Beam hardening** | Polychromatic X-ray spectrum (violates Beer-Lambert) | Cupping artifact (edges brighter than center), dark bands between dense objects |
| **Motion artifacts** | Patient movement during scan | Blurring, double edges, streaks |
| **Noise** | Low photon count (low dose) | Grainy/speckled appearance |

---

### 8.6 Quick-Reference Formulas (cheat sheet for the discussion)

| Concept | Formula |
|---------|---------|
| Beer-Lambert | `I = I₀ · e^(−∫μ dl)` |
| Projection (line integral) | `p = −ln(I/I₀) = ∫μ dl` |
| Radon Transform | `p(θ,s) = ∫∫ μ(x,y) δ(xcosθ + ysinθ − s) dx dy` |
| Fourier Slice Theorem | `F₁D{p(θ,·)}(ω) = F₂D{μ}(ωcosθ, ωsinθ)` |
| FBP filter step | `p_f = F⁻¹{|ω| · F{p}}` |
| FBP back projection | `μ(x,y) = ∫₀^π p_f(θ, xcosθ + ysinθ) dθ` |
| Poisson noise | `I_meas ~ Poisson(I₀ · e^(−∫μ dl))` |
| Noise vs dose | `σ ∝ 1/√I₀` |
| Hounsfield Units | `HU = 1000(μ − μ_w)/μ_w` |
| ART update | `x ← x + λ(bᵢ − aᵢx)aᵢᵀ / ‖aᵢ‖²` |

---

## 9. Potential Professor Questions & Model Answers

**Q: Walk me through what happens physically when we take one CT projection.**
> An X-ray tube emits a beam of photons. They pass through the patient and are attenuated according to Beer-Lambert's law — each tissue along the path absorbs some photons depending on its attenuation coefficient μ. The detector on the other side measures the remaining intensity I. We compute −ln(I/I₀) to get the line integral of μ along that ray. Repeating this for all detector positions at one angle gives us one projection (one column of the sinogram).

**Q: Why do we need many angles? Why not just one or two projections?**
> A single projection gives us line integrals — sums along lines. We can't determine the distribution of μ along each line from just the sum. By acquiring projections at many angles (ideally 0° to 180°), we get enough independent equations (line integrals) to uniquely determine μ(x,y) at every point. The Fourier Slice Theorem tells us each angle fills one line in 2D Fourier space — we need enough lines to adequately cover the full 2D frequency plane.

**Q: Explain the Fourier Slice Theorem in your own words.**
> If I take a projection of an object at angle θ and compute its 1D Fourier transform, I get the values of the object's 2D Fourier transform along a line through the origin at angle θ. So each projection "reveals" one slice of the 2D frequency information. Collecting projections at many angles fills in the 2D Fourier space, and then we can reconstruct the image by inverting.

**Q: Why filter before back-projecting? What happens without the filter?**
> Without filtering, back projection smears each projection value along the ray path it came from. The superposition of all these smeared projections produces a blurred version of the original image — mathematically convolved with a 1/r function. The ramp filter |ω| in the frequency domain counteracts this by boosting high frequencies, effectively deconvolving the blur. The result is a sharp, accurate reconstruction.

**Q: How would you reduce dose in CT, and what is the trade-off?**
> We can reduce dose by lowering the tube current (fewer photons I₀) or by acquiring fewer projections. Both degrade image quality: fewer photons increase Poisson noise (granular appearance), and fewer projections cause angular undersampling artifacts (streaks). The fundamental trade-off is dose versus image quality — the ALARA principle in clinical practice says use the minimum dose that still gives diagnostically acceptable images.

**Q: Why might iterative reconstruction be better than FBP for low-dose CT?**
> FBP treats all frequency components equally after filtering, so it amplifies noise along with signal. Iterative methods like ART solve the reconstruction as an optimization problem and can incorporate constraints — for example, enforcing that pixel values must be non-negative, or adding regularization that penalizes noisy solutions. This lets them produce cleaner images from the same noisy data, especially when projections are sparse.

---

## 10. Deliverables Checklist

- [ ] **Apr 6**: Short project description submitted
- [ ] **Apr 13**: Full proposal form submitted
- [ ] **Apr 30**: All source code in `src/`
- [ ] **Apr 30**: Experiment notebooks in `notebooks/` with results
- [ ] **Apr 30**: Presentation slides in `presentation/`
- [ ] **May 4**: Each member ready for individual Q&A
- [ ] Each member can explain the full pipeline end-to-end
- [ ] Each member has deep knowledge of their specific module
- [ ] All figures are publication-quality (labeled axes, titles, colorbars)
