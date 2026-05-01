# Streamlit MTF Review and Fix

## Context

The last two commits changed the FBP reconstruction scaling and narrowed the default MTF edge row range. The Streamlit app (`app.py`) uses the QA phantom to show an interactive reconstruction, MTF, NPS, CNR, and RMSE.

## What Was Correct

The FBP change is directionally correct. The forward projector uses normalized detector coordinates from `-1` to `1`, so the detector spacing is approximately:

```python
2.0 / (num_detectors - 1)
```

Scaling the ramp filter by `1 / detector_spacing` fixes a real reconstruction magnitude problem. Before that change, reconstructed attenuation values were much too small compared with the QA phantom values. The larger FFT padding is also reasonable because ramp filtering is implemented as convolution, and padding reduces circular wrap-around artifacts.

## Remaining Problem

The MTF fix only partially solved the issue. Narrowing the row range from the middle 60% of the image to the middle 20% avoids some unrelated structures, but the ESF extraction still averaged across the entire image width:

```python
edge_region = reconstruction[row_start:row_end, :]
esf = np.mean(edge_region, axis=0)
```

That means the ESF included more than the intended QA edge. It could include:

- the outer circular phantom boundary,
- both edges of the rectangular slab,
- unrelated reconstruction artifacts and noise.

Because edge-based MTF assumes one clean edge profile, averaging across the whole row made the MTF curve unstable. In a smoke test, the MTF values were finite but spiked far above `1`, which made the app's "10% MTF" number unreliable.

## Fix Applied

The ESF extraction now supports a localized profile around a single edge column. The Streamlit app uses the QA phantom metadata to pass the known right edge of the rectangular slab (`x_range_norm[1]`) into the MTF calculation.

This makes the app measure the intended QA edge instead of accidentally measuring the whole image row. The app also now reports "Not reached" for the 10% MTF metric when the curve never crosses the 10% threshold, instead of choosing the closest point and presenting it as a real crossing.

## Remaining Limitations

This is still a simple classroom-level edge MTF implementation. For publication-quality MTF, the next improvements would be:

- use a slanted edge instead of a perfectly vertical edge,
- apply controlled smoothing/windowing to the LSF,
- validate against a noiseless reconstruction and known reference.
