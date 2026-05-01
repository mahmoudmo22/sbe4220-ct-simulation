# Implementation Validation Review

## Scope

This review compares the current repository implementation against `documentation/implementation_plan.md`. It focuses on whether the code, notebooks, results, and Streamlit demo are enough for the final professor discussion.

## Overall Assessment

The core implementation is mostly complete. The project has all planned source modules:

- `src/phantom.py`
- `src/forward_projection.py`
- `src/noise_model.py`
- `src/fbp.py`
- `src/mtf.py`
- `src/nps.py`
- `src/cnr.py`
- `src/metrics.py`
- `src/utils.py`

The main CT pipeline exists and works:

```text
phantom -> forward projection -> Poisson noise -> FBP reconstruction -> metrics
```

The strongest part of the implementation is that it connects image quality to physics controls: dose, angular sampling, and reconstruction filter choice.

## What Is Strong

### Phantom Generation

Both planned phantom types exist:

- Shepp-Logan phantom for reconstruction quality.
- QA phantom for MTF, NPS, and CNR.

The QA phantom is especially useful for discussion because it contains explicit features:

- point insert,
- sharp edge insert,
- low-contrast CNR inserts,
- uniform background region.

### Forward Projection

The forward projector is implemented from scratch using parallel-beam geometry. It uses normalized coordinates and line-integral accumulation, which matches the plan and the course theory.

There are two versions:

- `generate_sinogram()`
- `generate_sinogram_fast()`

The Streamlit app now uses the faster version, which is better for live discussion.

### Noise Model

The Poisson noise model is implemented in the correct domain:

```text
line integral -> intensity -> Poisson photon count -> log transform
```

This is important because photon counting noise is Poisson in the intensity domain, not directly in the sinogram domain.

### FBP Reconstruction

FBP is implemented from scratch with multiple filters:

- Ram-Lak,
- Shepp-Logan,
- cosine,
- Hamming.

The recent detector-spacing scaling fix makes the reconstructed attenuation magnitudes much more physically reasonable.

### Metrics

The planned metrics are present:

- RMSE,
- SSIM,
- SNR,
- PSNR,
- MTF,
- NPS,
- CNR.

The Streamlit app now also shows the original phantom, reconstruction, error map, sinograms, and overlays for the metric regions.

## Numerical Sanity Checks

A small validation run was performed on a `64 x 64` phantom to check whether the main trends match the theory.

### Dose Trend

As dose decreases, CNR decreases and RMSE/NPS increase:

| I0 | CNR | RMSE | Mean NPS |
| ---: | ---: | ---: | ---: |
| `1e6` | `2.299` | `0.0086` | `0.000154` |
| `1e5` | `1.009` | `0.0105` | `0.000190` |
| `1e4` | `0.389` | `0.0221` | `0.000618` |
| `1e3` | `0.112` | `0.0651` | `0.004383` |

This supports the project claim that lower dose worsens noise and detectability.

### Angular Sampling Trend

For Shepp-Logan reconstruction, fewer projections worsen RMSE and SSIM:

| Projections | RMSE | SSIM |
| ---: | ---: | ---: |
| `180` | `0.3629` | `0.4300` |
| `90` | `0.3682` | `0.3812` |
| `45` | `0.3870` | `0.2897` |
| `20` | `0.5056` | `0.2256` |
| `10` | `0.7090` | `0.1717` |

This supports the angular undersampling/streak artifact story.

### Filter Trend

For QA reconstruction at fixed dose, smoother filters reduce both high-frequency MTF and NPS:

| Filter | MTF near 0.25 cyc/px | Mean NPS |
| --- | ---: | ---: |
| Ram-Lak | `0.605` | `0.000190` |
| Shepp-Logan | `0.546` | `0.000173` |
| Cosine | `0.430` | `0.000148` |
| Hamming | `0.321` | `0.000132` |

This supports the resolution-noise trade-off claim.

## Missing or Weak Parts

### Experiment 5 Is Not Fully Delivered

`notebooks/experiment_5_system_characterization.ipynb` exists, but it has no executed outputs. The expected result files are also missing:

- `results/exp5_visual.png`
- `results/exp5_mtf.png`
- `results/exp5_nps.png`

This matters because Experiment 5 is the final integrated characterization in the implementation plan.

### Experiment 6 Is Missing

The bonus detectability experiment is not present:

- no `notebooks/experiment_6_detectability.ipynb`
- no NEQ or `d'` result plot

This is acceptable if time is limited because it was marked as bonus, but it should not be claimed as implemented.

### Presentation Directory Differs From the Plan

The plan expects a `presentation/` directory. The repo instead has presentation-related files under `documentation/` and `results/`, plus a Google Drive link in `README.md`.

This is not a technical problem, but it is a deliverable organization mismatch.

### Notebook Generator Is Outdated

`generate_notebooks.py` still creates notebooks using older patterns:

- slow `generate_sinogram()` instead of `generate_sinogram_fast()`,
- edge MTF calls without passing the known QA edge column.

If this script is rerun, it may regenerate notebooks with weaker MTF behavior than the fixed Streamlit app.

### MTF Is Improved but Still Basic

The MTF implementation is now better for the app because it localizes the edge profile. However, it is still a simplified edge method:

- no slanted-edge oversampling,
- limited LSF smoothing/windowing,
- no robust monotonic 10% crossing enforcement,
- no external/reference validation.

For a course project, this is probably acceptable if explained honestly.

### NPS Uses Spatial ROIs From One Reconstruction

The NPS implementation extracts multiple ROIs from a reconstruction and averages their spectra. This is a common classroom approximation, but real NPS validation usually uses repeated noise realizations and carefully selected uniform ROIs.

The professor may ask this. The answer should be:

> We estimate NPS from multiple uniform ROIs in the QA phantom. A more rigorous clinical-style NPS would average over repeated noisy acquisitions.

### CNR Values May Be Below Rose Criterion

In the small validation run, even `I0 = 1e6` gave CNR below `3`. That does not mean the code is wrong. It means the low-contrast insert is subtle and reconstruction artifacts/noise are significant. For the demo, use the Streamlit control to show how CNR changes with dose, but do not promise that the default setup always passes Rose criterion.

## Recommended Next Actions

High priority:

1. Execute or regenerate `experiment_5_system_characterization.ipynb`.
2. Save the missing Experiment 5 result figures.
3. Update `generate_notebooks.py` to use `generate_sinogram_fast()` and pass the QA edge column for MTF.
4. Add Streamlit run instructions to `README.md`.

Medium priority:

1. Add a small validation notebook or section comparing expected trends:
   - dose vs CNR/NPS,
   - projections vs RMSE/SSIM,
   - filters vs MTF/NPS.
2. Add a short explanation of NPS limitations and MTF limitations in the presentation.
3. Add a simple summary table for Experiment 5 operating points.

Optional:

1. Add `experiment_6_detectability.ipynb` with a simple NEQ curve:

```text
NEQ(f) = MTF(f)^2 / NPS(f)
```

1. Add a Shepp-Logan visual-only mode to Streamlit for intuitive reconstruction quality.

## Final Recommendation

The implementation is strong enough for the professor discussion if the team focuses on the correct story:

- physics pipeline,
- dose/noise relationship,
- angular undersampling artifacts,
- FBP filter resolution-noise trade-off,
- why MTF, NPS, and CNR are more informative than only looking at images.

Before presentation, the most important cleanup is to complete Experiment 5 outputs and keep the notebooks/generator consistent with the fixed MTF approach.
