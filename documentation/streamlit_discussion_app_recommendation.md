# Streamlit Discussion App Recommendation

## Goal

The Streamlit app should be a live explanation tool for the professor discussion. It should not try to replace all experiment notebooks. The best role split is:

- **Streamlit app:** interactive story of the CT pipeline and immediate parameter effects.
- **Notebooks:** systematic sweeps, saved figures, and backup evidence for final results.

This is a good direction because the professor can ask, "What happens if dose decreases?" or "What happens with fewer projections?" and the team can show the answer immediately.

## Current Strengths

The current app already follows the core project pipeline:

```text
Phantom -> Sinogram -> Poisson noise -> FBP reconstruction -> MTF/NPS/CNR/RMSE
```

It also exposes the most important scanner/reconstruction controls:

- incident photon count `I0`,
- number of projection angles,
- FBP reconstruction filter.

These controls match the implementation plan well because they demonstrate the three main trade-offs:

- lower dose increases noise,
- fewer projections create streak artifacts,
- sharper filters improve resolution but amplify noise.

## What Was Missing

The previous app version showed the noisy sinogram, reconstruction, MTF, and NPS, but it did not show the original phantom. That made the reconstruction hard to judge visually because there was no ground truth next to it.

For professor discussion, the app should also show:

- the original QA phantom,
- the reconstructed image,
- the reconstruction error map,
- overlays showing where CNR, NPS, and MTF are measured.

Those visuals make the metrics defendable. Instead of only reporting a number, the presenter can point to the exact edge, insert, and uniform region used to compute it.

## Recommended Demo Flow

1. Start with high dose, many projections, and Ram-Lak.
2. Explain the QA phantom features: edge for MTF, uniform region for NPS, low-contrast insert for CNR.
3. Lower `I0` and show NPS increasing and CNR decreasing.
4. Reduce projection count and show streak artifacts and RMSE change.
5. Switch filters and explain the MTF/NPS trade-off.

## Implementation Priority

High priority:

- add original phantom display,
- add reconstruction error map,
- add reproducible noise seed control,
- add display window controls,
- add metric ROI/edge overlays.

Medium priority:

- add Shepp-Logan as a separate visual-only demo mode,
- add saved presets for common discussion scenarios,
- add small explanatory captions under each plot.

Low priority:

- expose detector spacing or ROI size controls,
- add advanced NEQ/detectability plots.

Those controls are useful scientifically, but they may distract from the main discussion unless the professor asks about them.

## Recommendation

Keep Streamlit as the main live demo. Keep notebooks as backup. The Streamlit app should remain focused on the QA phantom because this phantom directly supports MTF, NPS, CNR, and RMSE in one compact interactive view.
