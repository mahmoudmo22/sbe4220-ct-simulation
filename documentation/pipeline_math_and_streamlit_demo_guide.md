# Pipeline Math and Streamlit Demo Guide

## Purpose

This guide explains the full CT simulation pipeline module by module, including the mathematical model behind each step and the important clarifications to mention during professor discussion.

It also gives suggested Streamlit scenarios to demonstrate live.

## Big Picture Pipeline

```text
Phantom
-> Forward projection
-> Poisson noise model
-> Filtered back projection
-> Image quality metrics
-> Interactive visualization
```

The central question is:

> How do acquisition and reconstruction parameters affect image quality, spatial resolution, noise, and detectability?

The important controllable parameters in the Streamlit app are:

- incident photon count `I0`,
- number of projection angles,
- FBP reconstruction filter,
- noise seed,
- image display window.

## 1. Phantom Generation

Relevant module:

- `src/phantom.py`

### Phantom Role

This module creates the ground truth attenuation image `mu(x, y)`.

There are two phantom types:

- **Shepp-Logan phantom:** useful for visually showing CT reconstruction quality.
- **QA phantom:** useful for quantitative metrics.

The Streamlit app currently focuses on the QA phantom because it contains known features for measuring:

- MTF from a sharp edge,
- NPS from a uniform region,
- CNR from low-contrast inserts,
- RMSE by comparing reconstruction to ground truth.

### Phantom Math Model

Each pixel represents a linear attenuation coefficient:

```text
mu(x, y)
```

For the QA phantom, regions are defined geometrically:

- circular background disk,
- rectangular high-contrast edge insert,
- small point insert,
- circular low-contrast inserts.

For the Shepp-Logan phantom, the image is built from ellipses:

```text
((x') / a)^2 + ((y') / b)^2 <= 1
```

where `a` and `b` are ellipse semi-axes, and `(x', y')` are rotated coordinates.

### Phantom Discussion Clarification

Say:

> The phantom is the known ground truth. This lets us compare the reconstructed image against what we actually simulated.

Important note:

> The QA phantom is not meant to look like anatomy. It is a measurement phantom, like quality assurance phantoms used in medical physics.

## 2. Forward Projection

Relevant module:

- `src/forward_projection.py`

### Forward Projection Role

This module simulates parallel-beam X-ray acquisition. It generates the sinogram, where each column is one projection angle and each row is one detector bin.

### Physical Model

The physical model is Beer-Lambert attenuation:

```text
I = I0 * exp(- integral mu(x, y) dl)
```

The measured projection value after log transform is:

```text
p = -ln(I / I0) = integral mu(x, y) dl
```

### Forward Projection Math Model

The ideal continuous model is the Radon transform:

```text
p(theta, s) = integral integral mu(x, y) delta(x cos(theta) + y sin(theta) - s) dx dy
```

In the code, this is approximated by sampling points along each ray:

```text
line_integral ~= sum(mu(ray_samples)) * pixel_spacing
```

### Forward Projection Discussion Clarification

Say:

> The sinogram is the Radon transform of the phantom. A CT scanner does not directly measure the image; it measures many line integrals through the object.

Important note:

> We use parallel-beam geometry for simplicity. Real clinical CT commonly uses fan-beam or cone-beam geometry, but the reconstruction principles are easier to demonstrate with parallel beams.

## 3. Noise Model

Relevant module:

- `src/noise_model.py`

### Noise Model Role

This module simulates radiation dose by adding Poisson noise to photon counts.

Lower `I0` means fewer photons and more noise.

### Noise Math Model

Start from the clean line integral sinogram:

```text
p = integral mu dl
```

Convert to expected detected photons:

```text
I_expected = I0 * exp(-p)
```

Sample photon counts:

```text
I_measured ~ Poisson(I_expected)
```

Convert back to noisy sinogram:

```text
p_noisy = -ln(I_measured / I0)
```

### Dose-Noise Relationship

For Poisson statistics:

```text
variance = mean
standard deviation ~= sqrt(mean)
relative noise ~= 1 / sqrt(I)
```

So:

```text
noise ~= 1 / sqrt(I0)
```

### Noise Discussion Clarification

Say:

> Noise is added before the log transform because X-ray detectors count photons. Photon counts follow Poisson statistics.

Important note:

> Adding Gaussian noise directly to the sinogram is simpler, but less physically accurate.

## 4. Filtered Back Projection

Relevant module:

- `src/fbp.py`

### FBP Role

This module reconstructs the image from the sinogram using filtered back projection.

It supports these filters:

- Ram-Lak,
- Shepp-Logan,
- cosine,
- Hamming.

### FBP Math Model

Filtered back projection has two steps.

Step 1: filter each projection in frequency domain:

```text
p_filtered(theta, s) = F^-1 { |w| * F{p(theta, s)} }
```

Step 2: back-project the filtered projections:

```text
mu_hat(x, y) = integral_0^pi p_filtered(theta, x cos(theta) + y sin(theta)) d theta
```

In discrete code:

```text
mu_hat(x, y) ~= (pi / N_angles) * sum over theta p_filtered(theta, s)
```

### Why Filtering Is Needed

Simple back projection smears each projection back across the image. This causes blur.

The ramp filter `|w|` corrects the over-representation of low frequencies.

### Filter Trade-Off

Ram-Lak:

- preserves high frequencies,
- sharper image,
- more high-frequency noise.

Hamming/cosine:

- suppress high frequencies,
- smoother image,
- lower noise,
- lower spatial resolution.

### FBP Discussion Clarification

Say:

> The reconstruction filter is not just a cosmetic choice. It directly changes the resolution-noise trade-off, which we quantify using MTF and NPS.

Important note:

> The implementation uses normalized detector coordinates. The ramp filter must be scaled consistently with detector spacing, otherwise reconstructed attenuation magnitudes become wrong.

## 5. MTF: Spatial Resolution

Relevant module:

- `src/mtf.py`

### MTF Measurement Meaning

MTF, or Modulation Transfer Function, measures how well the system preserves contrast at different spatial frequencies.

High MTF at high frequency means better fine-detail resolution.

### MTF Math Model

For a point object:

```text
MTF(f) = |F{PSF}| / |F{PSF}(0)|
```

For an edge:

```text
ESF = edge spread function
LSF = d(ESF) / dx
MTF(f) = |F{LSF}| / |F{LSF}(0)|
```

### How the App Uses It

The app uses the QA phantom's sharp rectangular slab edge.

The important correction is that MTF should be extracted around one localized edge, not across the whole image row.

### MTF Discussion Clarification

Say:

> MTF tells us how contrast transfer changes with spatial frequency. A sharper filter should give higher high-frequency MTF, but it usually increases noise.

Important limitation:

> Our edge MTF is a simplified classroom implementation. A clinical-grade method would use a slanted edge, oversampling, windowing, and more careful validation.

## 6. NPS: Noise Texture

Relevant module:

- `src/nps.py`

### NPS Measurement Meaning

NPS, or Noise Power Spectrum, measures how image noise is distributed over spatial frequency.

Noise standard deviation gives one number. NPS tells us whether the noise is fine-grained or low-frequency/blotchy.

### NPS Math Model

Extract uniform ROIs and subtract their mean:

```text
noise_roi = ROI - mean(ROI)
```

Compute the 2D noise power spectrum:

```text
NPS(u, v) = (pixel_size^2 / (Nx * Ny)) * average(|FFT2(noise_roi)|^2)
```

Then radially average to get 1D NPS:

```text
NPS(f)
```

### NPS Discussion Clarification

Say:

> NPS is important because two images can have similar standard deviation but different noise texture.

Important limitation:

> This implementation estimates NPS from multiple ROIs in one reconstruction. A stricter medical physics approach would average over repeated noisy acquisitions.

## 7. CNR: Detectability

Relevant module:

- `src/cnr.py`

### CNR Measurement Meaning

CNR, or Contrast-to-Noise Ratio, measures whether a low-contrast object can be distinguished from its background.

### CNR Math Model

```text
CNR = |mean(insert ROI) - mean(background ROI)| / std(background ROI)
```

### Rose Criterion

A common rule of thumb:

```text
CNR >= 3 to 5
```

means the object is more reliably detectable by a human observer.

### CNR Discussion Clarification

Say:

> CNR combines contrast and noise into a detectability metric. When dose decreases, noise increases, so CNR drops.

Important note:

> The default setup may not always pass the Rose criterion because the low-contrast insert is intentionally subtle.

## 8. RMSE and SSIM

Relevant module:

- `src/metrics.py`

### RMSE and SSIM Meaning

RMSE compares reconstruction to the known ground truth:

```text
RMSE = sqrt(mean((reconstruction - phantom)^2))
```

SSIM measures structural similarity:

```text
SSIM compares local luminance, contrast, and structure
```

### RMSE and SSIM Discussion Clarification

Say:

> RMSE and SSIM are useful global image-quality metrics, but they do not explain whether degradation comes from blur, noise, or artifacts. That is why we also use MTF, NPS, and CNR.

## 9. Streamlit App

Relevant file:

- `app.py`

### Streamlit Display Contents

The app is designed as a live discussion dashboard. It shows:

- original QA phantom,
- reconstructed image,
- reconstruction error map,
- clean sinogram,
- noisy sinogram,
- MTF curve,
- NPS curve,
- CNR,
- RMSE,
- 10% MTF metric.

It also shows overlays for:

- MTF edge,
- CNR insert ROI,
- CNR background ROI,
- NPS ROI.

### Streamlit Discussion Clarification

Say:

> The app is not replacing the notebooks. The app is for live interactive explanation, while notebooks are for systematic experiment records.

## Streamlit Demo Scenarios

## Scenario 1: Baseline Good Acquisition

Recommended settings:

- `Log10(I0) = 6` or `7`
- projections = `180` or higher
- filter = `ram-lak`
- overlays = on

What to show:

- original phantom vs reconstruction,
- clean/noisy sinogram,
- CNR, RMSE, MTF, NPS.

How to explain:

> This is the reference case. We use many projections and high photon count, so noise and angular undersampling are relatively limited. The reconstruction should resemble the ground truth, and the error map should be moderate.

Key concept:

> More photons improve noise behavior, and more angles improve angular sampling.

## Scenario 2: Low Dose

Change only:

- reduce `Log10(I0)` from `6` or `7` down to `3` or `4`.

What to show:

- noisy sinogram becomes visibly noisier,
- reconstructed image becomes grainier,
- NPS magnitude increases,
- CNR decreases,
- RMSE increases.

How to explain:

> Lower dose means fewer detected photons. Since photon counts follow Poisson statistics, relative noise increases roughly as `1 / sqrt(I0)`. That noise propagates through the log transform and reconstruction.

Professor takeaway:

> This demonstrates the dose-image-quality trade-off and the ALARA principle.

## Scenario 3: Fewer Projection Angles

Change only:

- keep dose high,
- reduce projections from `180` to `45`, `20`, or `10`.

What to show:

- reconstruction develops streak artifacts,
- error map becomes structured,
- RMSE increases,
- MTF may degrade or become less stable.

How to explain:

> Each projection gives one set of line integrals. With too few angles, Fourier space is undersampled, so missing angular information appears as streak artifacts.

Professor takeaway:

> This demonstrates angular undersampling.

## Scenario 4: Filter Trade-Off

Keep:

- fixed dose,
- fixed projection count.

Switch filters:

- Ram-Lak,
- Shepp-Logan,
- cosine,
- Hamming.

What to show:

- Ram-Lak looks sharper but noisier,
- Hamming looks smoother but blurrier,
- high-frequency MTF decreases with smoother filters,
- NPS decreases with smoother filters.

How to explain:

> The ramp filter boosts high frequencies to recover detail, but noise also lives at high frequencies. Windowed filters suppress that noise, but they also reduce spatial resolution.

Professor takeaway:

> MTF and NPS together reveal the resolution-noise trade-off.

## Scenario 5: Same RMSE, Different Interpretation

Try:

- one case with low dose but many projections,
- one case with high dose but few projections.

What to show:

- both can have degraded RMSE,
- low dose looks noisy,
- few projections create streaks,
- NPS and visual error map help distinguish the degradation type.

How to explain:

> A single global metric like RMSE cannot tell us the full reason why image quality degraded. That is why we need system metrics like MTF, NPS, and CNR.

Professor takeaway:

> Different acquisition problems can produce different image-quality failures even when scalar metrics look similar.

## Scenario 6: Rose Criterion and Detectability

Use:

- QA phantom,
- overlays on,
- vary dose.

What to show:

- CNR changes with dose,
- the CNR insert ROI and background ROI are visible,
- CNR may fall below the Rose criterion.

How to explain:

> The Rose criterion says reliable detection usually needs CNR around 3 to 5. If dose is too low, noise increases and the insert becomes harder to detect.

Professor takeaway:

> CNR connects physics and clinical detectability.

## Suggested Presentation Script

Use this short flow:

1. "This is the ground truth QA phantom. It contains a known edge, uniform region, and low-contrast inserts."
2. "The forward projector computes line integrals through this phantom, producing a sinogram."
3. "Noise is added in the photon-counting domain using Poisson statistics."
4. "FBP reconstructs the image by filtering each projection and back-projecting."
5. "Now we evaluate quality: MTF for resolution, NPS for noise texture, CNR for detectability, and RMSE for global error."
6. "By changing dose, angles, and filter, we can see how each scanner parameter changes the final image and metrics."

## Questions You Should Be Ready For

### Why use the QA phantom instead of only Shepp-Logan?

Answer:

> Shepp-Logan is useful visually, but the QA phantom has known features for objective measurement: an edge for MTF, a uniform region for NPS, and inserts for CNR.

### Why add noise before the log transform?

Answer:

> Because the detector counts photons, and photon counts follow Poisson statistics. The log transform is applied after detection to recover line integrals.

### Why does Ram-Lak look sharper but noisier?

Answer:

> Ram-Lak boosts high frequencies. This restores edge detail but also amplifies high-frequency noise.

### Why is NPS better than just standard deviation?

Answer:

> Standard deviation gives total noise power only. NPS tells us the frequency distribution of that noise, which affects visual texture and detectability.

### Is this clinical-grade MTF/NPS?

Answer:

> It is a simplified educational implementation. It demonstrates the correct concepts, but clinical QA would require stricter acquisition protocols, repeated scans, slanted-edge methods, and validation.

## Final Advice

For the professor discussion, do not present the app as just a collection of plots. Present it as a cause-and-effect simulator:

```text
change scanner parameter -> observe sinogram/reconstruction -> explain metric change
```

The strongest story is:

```text
Dose controls noise.
Projection count controls angular sampling artifacts.
Filter choice controls the resolution-noise trade-off.
MTF, NPS, and CNR quantify those effects.
```
