# 2D CT Simulation & System Characterization
## Final Presentation Structure (Team 18)

This document outlines the exact slide-by-slide structure for your presentation. By assigning each phase to the corresponding team member, you will demonstrate equal contribution and a deep understanding of the course material.

---

### Slide 1: Title & Introduction
* **Speaker:** Mahmoud Mohamed
* **Text/Content:** 
  * "2D CT Simulation & System Characterization"
  * "SBE 4220 — Medical Imaging II"
  * List all 5 team members.
* **Goal:** Set the stage. Explain that the project objective was not just to write a CT simulator, but to build a pipeline capable of **quantitatively evaluating** scanner performance (MTF, NPS, CNR).

---

### Slide 2: Data Acquisition & Physics
* **Speaker:** Mahmoud Mohamed
* **Equations to Include:**
  * Beer-Lambert Law: $I = I_0 e^{-\int \mu(x,y) dl}$
  * Radon Transform: $p(s, \theta) = \int \int \mu(x,y) \delta(x\cos\theta + y\sin\theta - s) dx dy$
* **Visuals to Include:**
  * An image of the 2D Shepp-Logan Phantom.
  * The parallel-beam overlay diagram from `experiment_1_baseline.ipynb` (showing the red rays passing through the phantom).
* **Talking Points:** Explain how parallel rays simulate physical X-ray line integrals across the 2D slice.

---

### Slide 3: The Filtered Back-Projection (FBP) Algorithm
* **Speaker:** Mahmoud Bahaa
* **Equations to Include:**
  * Back-projection integral: $\mu(x,y) = \int_0^\pi p_{filtered}(\theta, x\cos\theta + y\sin\theta) d\theta$
* **Visuals to Include:**
  * Clean Sinogram plot vs. Final Reconstructed Image.
* **Talking Points:** 
  * Mention the **Fourier Slice Theorem**.
  * Explain *why* the Ramp Filter ($|w|$) is physically necessary to correct the polar-to-Cartesian sampling density, and why it causes high-frequency noise amplification.

---

### Slide 4: Noise & Dose Modeling
* **Speaker:** Mohamed Ashraf
* **Equations to Include:**
  * Poisson statistics: $I_{measured} \sim \text{Poisson}(I_{expected})$
  * The variance rule: $\frac{\sigma}{\mu} = \frac{1}{\sqrt{I_0}}$
* **Visuals to Include:**
  * High dose sinogram vs. Low dose sinogram side-by-side.
* **Talking Points:** 
  * Emphasize that noise is added in the *pre-log intensity domain*, not the sinogram domain, because photon counting is a Poisson process.
  * Explain that halving the dose increases noise by $\sqrt{2}$.

---

### Slide 5: Quantitative Evaluation Metrics
* **Speaker:** Rashed Mamdouh
* **Equations to Include:**
  * MTF equation: $\text{MTF}(f) = |\mathcal{F}\{\frac{d}{dx}\text{ESF}(x)\}|$
  * CNR equation: $\text{CNR} = \frac{|\mu_{insert} - \mu_{bg}|}{\sigma_{bg}}$
* **Visuals to Include:**
  * A screenshot of the QA phantom showing the edge used for MTF and the circles used for CNR.
* **Talking Points:** 
  * Briefly define MTF (Spatial Resolution), NPS (Noise Texture).
  * Explain the **Rose Criterion**: A tumor is only detectable by a human observer if CNR $\geq 3$.

---

### Slide 6: Experimental Results — Filters
* **Speaker:** Ammar Yasser
* **Visuals to Include:** 
  * The `exp2_mtf.png` and `exp2_nps.png` graphs from the `results/` folder.
* **Talking Points:** 
  * Show the fundamental tradeoff: Ram-Lak has the highest spatial resolution (best MTF) but the most high-frequency noise (worst NPS). Hamming sacrifices resolution to suppress noise.

---

### Slide 7: Experimental Results — Dose & Projections
* **Speaker:** Ammar Yasser
* **Visuals to Include:** 
  * The CNR vs Dose curve (`exp3_cnr.png`).
  * The MTF vs Projections curve (`exp4_mtf.png`).
* **Talking Points:** 
  * Point to the exact dose level where the CNR curve drops below the Rose Criterion line (3.0).
  * Show how dropping from 360 to 45 angles destroys the high-frequency MTF response.

---

### Slide 8: Live Dashboard Demonstration!
* **Speaker:** Any team member (or transition between members)
* **Visuals:** 
  * A live screen share of the Streamlit App (`http://localhost:8501`).
* **Action:**
  * Drag the sliders live in front of the professor. 
  * Lower the dose and watch the CNR fail the Rose Criterion.
  * Change the filter to Hamming and watch the MTF curve shift downwards.
* **Closing:** "This tool allows us to characterize any theoretical 2D CT scanner instantly."
