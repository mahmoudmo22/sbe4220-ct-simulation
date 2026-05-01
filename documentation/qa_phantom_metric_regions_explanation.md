# QA Phantom Metric Regions Explanation

## Visual Being Discussed

File:

```text
presentation/visuals/slide05_qa_phantom_metric_regions.png
```

This figure shows the QA phantom and the regions used to compute the main system performance metrics:

- MTF: spatial resolution,
- NPS: noise texture,
- CNR: detectability.

## Do These Regions Make Sense?

Yes. The selected regions are reasonable for a classroom CT system-characterization project.

They match the QA phantom design:

- a sharp rectangular slab for edge-based MTF,
- a central uniform region for NPS and background noise,
- a low-contrast circular insert for CNR.

The main limitation is that these are simplified educational ROIs, not strict clinical/AAPM measurement protocols.

## Region 1: MTF Edge

Visual marker:

- cyan vertical line

Location:

- on the right edge of the bright rectangular slab.

### Why the MTF Edge Is Used

MTF measures spatial resolution. To estimate MTF using the edge method, we need a sharp edge.

The QA phantom contains a high-contrast rectangular slab. The right boundary of this slab is a nearly vertical step edge:

```text
background attenuation -> bright slab attenuation
```

The reconstruction blurs this sharp transition. The amount of blur tells us about spatial resolution.

### MTF Mathematical Idea

From the reconstructed edge:

```text
ESF = Edge Spread Function
```

Differentiate it:

```text
LSF = d(ESF) / dx
```

Then compute:

```text
MTF(f) = |FFT(LSF)| / |FFT(LSF)(0)|
```

### MTF Talking Point

> The cyan line marks the edge used for edge-based MTF. We extract a profile across this sharp transition, differentiate it to get the line spread function, and then take its Fourier transform to estimate spatial resolution.

### MTF Caveat

This is a simplified edge MTF. A clinical-grade method would usually use a slanted edge and oversampling. Here, the goal is educational: to show how filter choice affects spatial resolution.

## Region 2: CNR Insert

Visual marker:

- green circle

Location:

- around the lower-right low-contrast circular insert.

### Why the CNR Insert Is Used

CNR measures object detectability. The low-contrast insert represents a subtle object that should be detected against the background.

The green ROI measures the average reconstructed intensity inside the insert.

### CNR Insert Mathematical Idea

The insert mean is:

```text
mu_insert = mean(green ROI)
```

This is compared with the background mean and noise:

```text
CNR = |mu_insert - mu_background| / sigma_background
```

### CNR Insert Talking Point

> The green circle is the target object for CNR. It is intentionally low contrast, so its detectability depends strongly on the noise level.

### CNR Insert Caveat

The ROI is smaller than the actual insert radius to avoid edge partial-volume effects. This is why the circle does not cover the full visible insert.

## Region 3: CNR Background

Visual marker:

- yellow circle

Location:

- in the central uniform background area.

### Why the CNR Background Is Used

CNR needs a reference background region. The yellow circle is placed in a relatively uniform region of the phantom, away from the high-contrast slab and low-contrast inserts.

It provides:

```text
mu_background = mean(yellow ROI)
sigma_background = std(yellow ROI)
```

### CNR Background Talking Point

> The yellow circle estimates the background mean and background noise. CNR compares the green insert against this background.

### CNR Background Caveat

The background ROI must avoid structures and edges. If it overlaps an edge or artifact, the standard deviation would include structure instead of pure noise, making CNR misleading.

## Region 4: NPS ROI

Visual marker:

- magenta dashed square

Location:

- centered around the uniform background region.

### Why the NPS ROI Is Used

NPS measures the frequency content of noise. For this, we need a region that should be uniform in the true phantom.

The NPS calculation subtracts the mean from each ROI:

```text
noise_roi = ROI - mean(ROI)
```

Then it computes:

```text
NPS(u, v) = |FFT2(noise_roi)|^2
```

and radially averages it to obtain:

```text
NPS(f)
```

### NPS Talking Point

> The magenta square marks a uniform region used for NPS. Since the true object is approximately constant there, variations inside that ROI mainly represent noise and reconstruction texture.

### NPS Caveat

In the actual `compute_nps()` function, multiple ROIs are sampled around the center region. The magenta square is a representative visual marker, not necessarily every ROI used internally.

## Why the ROIs Are Not Placed on the Same Object

Each metric needs a different kind of structure:

| Metric | Needs | Region |
| --- | --- | --- |
| MTF | sharp edge | cyan slab edge |
| CNR | low-contrast target + background | green/yellow circles |
| NPS | uniform noisy region | magenta square |

So it is correct that the ROIs are in different parts of the phantom.

## Short Defense Script

Use this if asked:

> This QA phantom was designed so each metric has a known measurement target. The cyan line is a sharp edge for MTF, the green circle is a low-contrast target for CNR, the yellow circle is the background reference for CNR, and the magenta square marks a uniform region for NPS. These placements avoid mixing different structures, because MTF needs an edge, CNR needs an insert and background, and NPS needs a uniform area.

## Limitations to Mention Honestly

The regions are scientifically reasonable, but simplified:

- The MTF edge is vertical, not slanted.
- The NPS estimate uses spatial ROIs rather than repeated acquisitions.
- The CNR background ROI can be affected by reconstruction artifacts if the image quality is poor.
- ROI placement is based on known phantom geometry, not manual clinical segmentation.

## Best Slide Caption

Recommended caption:

> QA phantom metric regions: cyan edge for MTF, green insert and yellow background for CNR, and magenta uniform ROI for NPS estimation.
