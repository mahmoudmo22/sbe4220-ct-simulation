# Implementation Plan — 2D CT Simulation & System Performance Characterization

## Team 18: 5 Members | Course: SBE 4220 — Medical Imaging II | Spring 2026

### Team Members
| #  | Name              |
|----|-------------------|
| 1  | Mahmoud Mohamed   |
| 2  | Mahmoud Bahaa     |
| 3  | Mohamed Ashraf    |
| 4  | Rashed Mamdouh    |
| 5  | Ammar Yasser      |

---

## 1. Project Overview

Build a Python-based 2D CT simulator that covers the full pipeline **and** quantitatively evaluates system performance using medical-physics metrics (MTF, NPS, CNR):

```
Phantom → Forward Projection (Sinogram) → Add Noise → Reconstruction → Performance Evaluation
```

### What makes this project unique

Most CT simulation projects stop at "reconstruct and show it looks good." This project goes further by asking **"how good is it, quantitatively?"** — measuring spatial resolution (MTF), noise characteristics (NPS), and object detectability (CNR) under varying conditions. This is how real CT systems are evaluated in clinical medical physics.

### Modules

| Module | Description |
|--------|-------------|
| **Phantom Generator** | Shepp-Logan phantom for reconstruction + specialized QA phantoms for MTF/NPS/CNR |
| **Forward Projector** | Simulate X-ray acquisition using ray-tracing + Beer-Lambert law |
| **Noise Model** | Add realistic Poisson noise to simulate different dose levels |
| **Reconstruction (FBP)** | Filtered Back Projection with multiple filter options |
| **Performance Metrics** | MTF (spatial resolution), NPS (noise texture), CNR (detectability) |
| **Analysis & Visualization** | Systematic parameter sweeps, comparison plots, summary tables |

---

## 2. Timeline

| Week | Dates | Milestone |
|------|-------|-----------|
| **Week 1** | Apr 6 – Apr 12 | Submit short description. All members study core theory. Set up repo, agree on code structure. |
| **Week 2** | Apr 13 – Apr 19 | Submit full proposal. Phantom + Forward Projector complete. Basic FBP working. |
| **Week 3** | Apr 20 – Apr 26 | Noise model complete. MTF/NPS/CNR modules working. All experiments running. |
| **Week 4** | Apr 27 – Apr 30 | Final integration, presentation slides, code cleanup. Submit by Apr 30. |
| **Presentation** | May 4 | Individual Q&A with professor. |

---

## 3. Task Division (5 Members)

### Mahmoud Mohamed — Phantom Generation & Forward Projection

**Responsibilities:**
- Implement the Shepp-Logan phantom generator (parameterized ellipses)
- Design and implement the **QA phantom** for metrics: a disk with embedded features
  - A small high-contrast point/wire for PSF/MTF measurement
  - A sharp edge for edge-spread-function (ESF) based MTF measurement
  - Low-contrast inserts at known μ values for CNR measurement
  - A uniform region for NPS measurement
- Implement the forward projector: parallel-beam ray-tracing
- Generate sinograms for different numbers of projection angles (e.g., 360, 180, 90, 45, 20)

**Must understand:**
- Beer-Lambert law and how line integrals of μ(x,y) produce projection values
- How the sinogram is structured (rows = detector bins, columns = angles)
- Why the QA phantom needs specific geometric features for each metric

---

### Mahmoud Bahaa — FBP Reconstruction & Filter Analysis

**Responsibilities:**
- Implement Filtered Back Projection from scratch (not just calling a library)
- Implement multiple filters: Ram-Lak (ramp), Shepp-Logan, cosine, Hamming-windowed ramp
- Reconstruct from sinograms and provide to other members for quantitative analysis
- Visualize the visual effect of each filter

**Must understand:**
- The Fourier Slice Theorem (the theoretical foundation of FBP)
- Why filtering is necessary (the 1/r blurring problem in naive back projection)
- The frequency-domain interpretation of each filter (ramp boosts high freq, windows suppress it)
- How to implement the filter-then-backproject pipeline
- How filter choice affects the resolution-noise trade-off (the core connection to MTF/NPS)

---

### Mohamed Ashraf — Noise Modeling & Dose Simulation

**Responsibilities:**
- Implement Poisson noise model on raw projection data (pre-log domain)
- Simulate different dose levels by varying I₀ (incident photon count): 10⁶, 10⁵, 10⁴, 10³
- Reconstruct noisy sinograms and provide to Rashed for NPS/CNR analysis
- Generate dose-vs-quality curves (SNR, RMSE, SSIM as functions of I₀)
- Study and visualize noise propagation through the reconstruction pipeline

**Must understand:**
- Poisson statistics: why photon counting follows Poisson distribution
- The relationship between dose (I₀), noise variance, and image SNR
- How noise propagates through the log transform and into reconstruction
- ALARA principle (clinical motivation for dose reduction)
- The difference between pixel-level noise metrics (SNR) and the frequency-domain noise description (NPS)

---

### Rashed Mamdouh — System Performance Metrics (MTF, NPS, CNR)

**Responsibilities:**
- **MTF (Modulation Transfer Function):**
  - Extract the Point Spread Function (PSF) from reconstruction of a point/wire phantom
  - Compute MTF = |FFT(PSF)| (normalized)
  - Alternative: edge method — reconstruct a sharp edge, compute Edge Spread Function (ESF), differentiate to get Line Spread Function (LSF), FFT to get MTF
  - Plot MTF curves for different filters and different numbers of projections
- **NPS (Noise Power Spectrum):**
  - Extract uniform ROIs from noisy reconstructions
  - Compute 2D NPS = |FFT(noise image)|² averaged over multiple ROIs
  - Take radial average to get 1D NPS(f)
  - Plot NPS curves for different dose levels and different filters
- **CNR (Contrast-to-Noise Ratio):**
  - Measure mean and std in two ROIs (insert vs. background) from the QA phantom
  - CNR = |μ_insert − μ_background| / σ_background
  - Plot CNR vs. dose and CNR vs. number of projections
- Lead the integrated analysis: "How do MTF, NPS, and CNR together describe system performance?"

**Must understand:**
- What MTF physically means: the system's ability to reproduce contrast at each spatial frequency
- What NPS physically means: how noise power is distributed across frequencies
- What CNR physically means: ability to distinguish an object from its background
- How MTF and NPS together determine detectability (the NEQ concept, qualitatively)
- How filter choice creates a direct trade-off: sharper filter → higher MTF at high freq → but also higher NPS at high freq

---

### Ammar Yasser — Experiments, Analysis & Presentation

**Responsibilities:**
- Design and execute all systematic experiments (parameter sweeps across projections, dose, filters)
- Compute basic image quality metrics (RMSE, SSIM, SNR) across all experiments
- Produce all comparison plots, summary tables, and publication-quality figures
- Lead presentation slide preparation and final integration
- Co-lead the integrated system characterization (Experiment 5)

**Must understand:**
- What RMSE, SSIM, and SNR measure and their limitations as image quality metrics
- How to design a systematic parameter sweep and present results clearly
- The big picture: how all modules connect (phantom → sinogram → noise → reconstruction → metrics)
- How MTF, NPS, and CNR provide a more complete picture than basic metrics alone

---

## 4. Shared Responsibilities (All Members)

- **Everyone** must understand the full pipeline and be able to explain any part
- **Everyone** prepares for the professor's Q&A individually
- **Everyone** should understand what MTF, NPS, and CNR mean at a conceptual level
- Code reviews: each member reviews at least one other member's module
- Presentation: each member presents their module (~4 min each)

---

## 5. Suggested Tools & Libraries

| Tool | Purpose |
|------|---------|
| **Python 3.10+** | Primary language |
| **NumPy** | Array operations, FFT, linear algebra |
| **Matplotlib** | Visualization and plotting |
| **scikit-image** | Reference implementations for validation (e.g., `skimage.transform.radon`) — use ONLY for validation, not as your main implementation |
| **SciPy** | Interpolation, signal processing utilities |
| **CTLab** (optional) | Reference simulator to validate your results against |

**Important:** The core algorithms (forward projection, FBP, MTF/NPS/CNR computation) should be implemented from scratch to demonstrate understanding. Library functions can be used for validation only.

---

## 6. Experiments to Run

### Experiment 1: Baseline Reconstruction Quality
- Reconstruct the Shepp-Logan phantom using FBP with 360, 180, 90, 45, 20, and 10 projection angles
- Visual comparison + RMSE and SSIM as basic metrics
- Show streak artifacts appearing as angles decrease

### Experiment 2: Filter Comparison — Visual & Quantitative
- Reconstruct the same noisy sinogram using Ram-Lak, Shepp-Logan, cosine, and Hamming filters
- **Measure MTF for each filter** — show how Ram-Lak preserves high frequencies while Hamming rolls off
- **Measure NPS for each filter** — show how Ram-Lak amplifies high-frequency noise while Hamming suppresses it
- Key insight: filters trade resolution (MTF) for noise (NPS)

### Experiment 3: Dose vs. Image Quality (Comprehensive)
- Fix 180 projections, vary I₀ from 10⁶ down to 10³ photons
- For each dose level, measure:
  - Visual noise appearance
  - NPS curves (show noise power increasing and shifting)
  - CNR for the low-contrast insert (show detectability dropping)
  - RMSE and SSIM
- Plot all metrics vs. dose in a single summary figure

### Experiment 4: MTF vs. Number of Projections
- Fix dose (I₀ = 10⁵), vary number of projections
- Measure MTF for each — show how spatial resolution degrades with fewer projections
- Combine with NPS to give a complete picture

### Experiment 5: Integrated System Characterization
- Pick 3-4 representative "operating points" (e.g., high-dose/many-angles, low-dose/many-angles, high-dose/few-angles, low-dose/few-angles)
- For each, show side-by-side: reconstruction image, MTF curve, NPS curve, CNR value
- Create a summary table comparing all operating points
- Discuss which operating point gives the "best" trade-off and why

### Experiment 6 (Bonus): Detectability Index
- Combine MTF and NPS into a simple detectability index: d' = CNR × (task-dependent weighting)
- Or compute NEQ(f) = MTF²(f) / NPS(f) — the noise-equivalent quanta
- This is the "advanced" cherry on top — shows deep systems-level understanding

---

## 7. Code Structure

```
imaging_project/
├── documentation/
│   ├── requrments.md
│   ├── project_description.md
│   └── implementation_plan.md
├── src/
│   ├── phantom.py              # Shepp-Logan + QA phantom generation
│   ├── forward_projection.py   # Ray-tracing, sinogram generation
│   ├── noise_model.py          # Poisson noise, dose simulation
│   ├── fbp.py                  # Filtered Back Projection + filters
│   ├── mtf.py                  # MTF measurement (PSF method + edge method)
│   ├── nps.py                  # NPS computation (2D → radial average → 1D)
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
HU = 1000 × (μ − μ_water) / μ_water
```
- Water = 0 HU, air = −1000 HU, bone ≈ +1000 HU
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

### 8.4 System Performance Metrics (THE UNIQUE PART — everyone must understand)

This section is what sets your project apart. Every team member must be able to explain these concepts.

#### 8.4.1 Modulation Transfer Function (MTF)

**What it is:** MTF describes how well the CT system preserves contrast at each spatial frequency. MTF(f) = 1 means perfect reproduction; MTF(f) = 0 means that frequency is completely lost.

**How to measure it:**

*Method 1 — Point Spread Function (PSF):*
1. Reconstruct a tiny point object (impulse) → the reconstruction is the PSF (it will be blurred/spread)
2. MTF = |FFT(PSF)|, normalized so MTF(0) = 1

*Method 2 — Edge Spread Function (ESF):*
1. Reconstruct a sharp edge (step function)
2. Extract a profile across the edge → this is the ESF
3. Differentiate ESF → Line Spread Function (LSF)
4. MTF = |FFT(LSF)|, normalized

**Math:**
```
PSF(x,y) = system response to δ(x,y)
MTF(u,v) = |F{PSF(x,y)}|
For 1D:  MTF(f) = |F{LSF(x)}|
```

**Key insight:** The reconstruction filter directly shapes the MTF:
- Ram-Lak → MTF stays high at high frequencies (sharp images, but noisy)
- Hamming → MTF rolls off at high frequencies (smoother images, less noise)

**Be ready to answer:**
- "What does MTF physically mean?" → It tells you the fraction of contrast that the system preserves at each spatial frequency. An MTF of 0.5 at frequency f means the system reproduces features at that frequency with half the original contrast.
- "How does the reconstruction filter affect MTF?" → A sharper filter (Ram-Lak) preserves high-frequency contrast, giving higher MTF at high frequencies. A smoother filter (Hamming) attenuates high frequencies, lowering the MTF but also reducing noise.
- "What limits the MTF in your simulation?" → Pixel size (discrete sampling), number of projections (angular sampling), detector bin width, and the reconstruction filter.

#### 8.4.2 Noise Power Spectrum (NPS)

**What it is:** NPS describes the frequency content of noise. Unlike a single standard deviation (σ), NPS tells you *where* the noise energy sits in the frequency domain. This matters because noise at different frequencies affects image quality differently.

**How to measure it:**
1. Reconstruct a uniform phantom with noise (multiple realizations)
2. Extract multiple small square ROIs from the uniform region
3. Subtract the mean from each ROI (isolate the noise)
4. Compute |FFT(noise ROI)|² for each ROI
5. Average over all ROIs → 2D NPS
6. Take radial average → 1D NPS(f)

**Math:**
```
NPS(u,v) = (Δx·Δy / Nx·Ny) · ⟨|FFT{ROI − mean(ROI)}|²⟩
```
where ⟨·⟩ denotes averaging over multiple ROIs, Δx/Δy are pixel sizes, Nx/Ny are ROI dimensions.

**Key insight:** The reconstruction filter shapes the NPS too:
- Ram-Lak → NPS peaks at high frequencies (noisy, grainy texture)
- Hamming → NPS is suppressed at high frequencies (smoother noise)
- This is the OTHER side of the MTF trade-off

**Be ready to answer:**
- "Why not just use standard deviation to describe noise?" → Standard deviation is a single number that gives the total noise power. NPS tells you how that noise is distributed across frequencies. Two images can have the same σ but very different noise textures — one could be grainy (high-freq noise) and the other could be blobby (low-freq noise). NPS captures this distinction.
- "How does dose affect NPS?" → Lower dose increases overall NPS magnitude (more noise power at all frequencies). The shape of NPS depends mainly on the filter, while the magnitude scales with 1/dose.
- "What is the relationship between NPS and noise variance?" → The integral of NPS over all frequencies equals the noise variance σ²: `σ² = ∫∫ NPS(u,v) du dv`.

#### 8.4.3 Contrast-to-Noise Ratio (CNR)

**What it is:** CNR measures how distinguishable an object (insert) is from its surrounding background. It's the most clinically intuitive metric — "can you see the lesion?"

**How to measure it:**
1. Place an insert with known attenuation (μ_insert) in a uniform background (μ_background)
2. Reconstruct with noise
3. Draw ROIs in the insert and in the background
4. CNR = |mean(ROI_insert) − mean(ROI_background)| / std(ROI_background)

**Math:**
```
CNR = |μ_insert − μ_background| / σ_background
```

**Key insight:** CNR depends on both contrast AND noise. You can improve CNR by:
- Increasing dose (reduces σ) — but more radiation to patient
- Using a smoother filter (reduces σ) — but loses spatial resolution
- Increasing contrast (larger μ difference) — not under our control clinically

**Be ready to answer:**
- "What CNR value is needed to detect a lesion?" → The Rose criterion: CNR ≈ 3–5 is typically needed for reliable visual detection by a human observer.
- "How does CNR change with dose?" → CNR ∝ √I₀ (since σ ∝ 1/√I₀ and contrast is independent of dose). Doubling the dose improves CNR by √2.

#### 8.4.4 How MTF, NPS, and CNR Fit Together

This is the "big picture" insight your professor will love:

```
                    ┌─────────────┐
                    │  CT System  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────▼────┐  ┌────▼────┐  ┌────▼────┐
         │   MTF   │  │   NPS   │  │   CNR   │
         │(resoln) │  │ (noise) │  │(detect) │
         └────┬────┘  └────┬────┘  └────┬────┘
              │            │            │
              └────────────┼────────────┘
                           │
                    ┌──────▼──────┐
                    │    NEQ(f)   │
                    │ = MTF²/NPS │
                    └─────────────┘
```

- **MTF** tells you what the system can resolve (signal transfer)
- **NPS** tells you what noise the system adds (noise character)
- **CNR** gives a single-number summary of detectability for a specific object
- **NEQ** (bonus) combines MTF and NPS into a frequency-dependent "efficiency" measure

A good CT system has: high MTF, low NPS, and high CNR. But these compete — the reconstruction filter that maximizes MTF (Ram-Lak) also maximizes NPS. The "optimal" filter depends on the clinical task.

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
| MTF (from PSF) | `MTF(f) = \|FFT{PSF}\| / \|FFT{PSF}\|_{f=0}` |
| MTF (from edge) | `MTF(f) = \|FFT{d/dx(ESF)}\|` normalized |
| NPS | `NPS(f) = ⟨\|FFT{ROI − mean}\|²⟩ · Δx²/(Nx·Ny)` |
| CNR | `CNR = \|μ₁ − μ₂\| / σ_background` |
| NEQ (bonus) | `NEQ(f) = MTF²(f) / NPS(f)` |
| Rose criterion | Detection requires CNR ≥ 3–5 |

---

## 9. Potential Professor Questions & Model Answers

### Core CT Questions (all members)

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

### Performance Metrics Questions (the differentiator)

**Q: Why use MTF instead of just looking at the image?**
> Visual inspection is subjective. MTF gives an objective, quantitative measure of spatial resolution as a function of frequency. It tells us exactly at which spatial frequency the system starts losing contrast. Two systems might look "similarly sharp" by eye but have measurably different MTF curves — one might preserve fine details better than the other. MTF is the standard metric used in medical physics for CT system acceptance testing and quality assurance.

**Q: How do you measure MTF from your simulation?**
> We use two methods. First, the PSF method: we reconstruct a tiny point object — the reconstruction is the Point Spread Function. We take its FFT magnitude and normalize to get MTF. Second, the edge method: we reconstruct a sharp edge, extract the edge profile (ESF), differentiate to get the Line Spread Function (LSF), and take its FFT. The edge method is more robust in practice because a point source has very low SNR, while an edge provides more signal.

**Q: Why is NPS better than just reporting noise standard deviation?**
> Standard deviation gives a single number — the total noise power. But two images can have the same σ with completely different noise *textures*. One might have fine-grained noise (high-frequency dominant), another might have coarse blobby noise (low-frequency dominant). NPS decomposes the noise into its frequency components, telling us exactly where the noise energy sits. This matters clinically because noise at certain frequencies interferes more with diagnostic tasks than noise at other frequencies.

**Q: How does the reconstruction filter affect both MTF and NPS?**
> The filter directly shapes both. The Ram-Lak (ramp) filter weights frequencies by |ω|, which boosts high frequencies — this gives high MTF at high frequencies (sharp images) but also amplifies high-frequency noise (high NPS at high frequencies). A Hamming-windowed filter rolls off the high frequencies — lower MTF (less sharp) but also lower NPS (less noise). This is the fundamental resolution-noise trade-off in FBP, and MTF/NPS make it quantitatively visible.

**Q: What is the Rose criterion and how does it connect to CNR?**
> The Rose criterion states that an object must have a CNR of approximately 3 to 5 to be reliably detected by a human observer. Below this threshold, the object is buried in noise and cannot be distinguished from background fluctuations. In our simulation, we can show that as we reduce dose, CNR drops below this threshold, and the inserts become visually undetectable — confirming the criterion experimentally.

**Q: What is NEQ and why is it useful?**
> NEQ (Noise-Equivalent Quanta) combines MTF and NPS into a single frequency-dependent metric: NEQ(f) = MTF²(f) / NPS(f). It represents the effective number of photons contributing to the image at each frequency — after accounting for both the signal transfer (MTF) and the noise (NPS). A higher NEQ means better image quality at that frequency. It's useful because it provides a unified measure of system performance that accounts for both resolution and noise simultaneously.

---

## 10. Deliverables Checklist

- [ ] **Apr 6**: Short project description submitted
- [ ] **Apr 13**: Full proposal form submitted
- [ ] **Apr 30**: All source code in `src/`
- [ ] **Apr 30**: Experiment notebooks in `notebooks/` with results
- [ ] **Apr 30**: Presentation slides in `presentation/`
- [ ] **May 4**: Each member ready for individual Q&A
- [ ] Each member can explain the full pipeline end-to-end
- [ ] Each member can explain MTF, NPS, and CNR conceptually
- [ ] Each member has deep knowledge of their specific module
- [ ] All figures are publication-quality (labeled axes, titles, colorbars, proper units on frequency axes)

---

## 11. Recommended Study Resources

- **Prince & Links, Medical Imaging: Signals and Systems (2nd ed.)** — Chapters 6–7 for CT physics and reconstruction
- **AAPM Report 233** — CT image quality metrics (MTF, NPS methodology). Search for "AAPM CT performance evaluation" for practical guidance.
- **Bushberg et al., The Essential Physics of Medical Imaging** — Chapter 10 for CT, good supplementary reference
- **ICRU Report 87** — Radiation dose and image quality for CT (background reading on dose-quality trade-offs)
