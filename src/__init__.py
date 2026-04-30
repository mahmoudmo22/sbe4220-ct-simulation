"""
CT Simulation Project — Source Package
=======================================

A complete numerical simulation of a 2D X-ray CT pipeline with
quantitative system performance characterisation.

Modules:
    phantom             — Shepp-Logan and QA phantom generation
    forward_projection  — Parallel-beam ray-tracing, sinogram generation
    noise_model         — Poisson noise, dose simulation
    fbp                 — Filtered Back Projection + filter kernels
    mtf                 — Modulation Transfer Function measurement
    nps                 — Noise Power Spectrum characterisation
    cnr                 — Contrast-to-Noise Ratio measurement
    metrics             — Basic image quality metrics (RMSE, SSIM, SNR)
    utils               — Display, ROI, I/O utilities
"""
