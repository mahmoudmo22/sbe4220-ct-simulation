import json
import os

os.makedirs('notebooks', exist_ok=True)

def create_notebook(filename, cells_data):
    nb = {
        "cells": [],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "name": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 4
    }
    
    for ctype, content in cells_data:
        source = [line + '\n' for line in content.split('\n')]
        if source:
            source[-1] = source[-1].rstrip('\n')
            
        if ctype == 'md':
            nb['cells'].append({
                "cell_type": "markdown",
                "metadata": {},
                "source": source
            })
        elif ctype == 'code':
            nb['cells'].append({
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": source
            })
            
    with open(f'notebooks/{filename}', 'w') as f:
        json.dump(nb, f, indent=1)

theory_cells = [
    ('md', '# 2D CT Simulation Pipeline: Theory & Equations\n\nThis notebook explains the mathematical and physical foundations of our CT Simulation pipeline, strictly following the equations from **Medical Imaging Signals and Systems (Prince & Links)**.'),
    ('md', '## 1. Forward Projection (Data Acquisition)\n\nThe physical process of X-rays passing through a patient is governed by the **Beer-Lambert Law**:\n\n$$ I = I_0 e^{-\\int \\mu(x,y) dl} $$\n\nWhere:\n* $I_0$ is the incident X-ray intensity (number of photons).\n* $I$ is the detected intensity.\n* $\\mu(x,y)$ is the linear attenuation coefficient of the tissue at location $(x,y)$.\n\nBy taking the negative natural logarithm, we isolate the line integral, which is our projection data $p$:\n\n$$ p = -\\ln\\left(\\frac{I}{I_0}\\right) = \\int \\mu(x,y) dl $$\n\n### The Radon Transform\nIn our code (`src/forward_projection.py`), we simulate parallel-beam geometry. This means $p$ is the **Radon Transform** of the object, defined by the line $s = x\\cos\\theta + y\\sin\\theta$:\n\n$$ p(s, \\theta) = \\int_{-\\infty}^{\\infty} \\int_{-\\infty}^{\\infty} \\mu(x,y) \\delta(x\\cos\\theta + y\\sin\\theta - s) dx dy $$\n\nTo compute this discretely, we trace parallel rays across the image grid. The parametric equations for a ray at offset $s$ and angle $\\theta$ are:\n\n$$ x(t) = s\\cos\\theta - t\\sin\\theta $$\n$$ y(t) = s\\sin\\theta + t\\cos\\theta $$'),
    ('code', '# Example: Generating the clean Sinogram p(s, theta)\nimport os, sys\nsys.path.append(os.path.abspath("../src"))\nfrom phantom import generate_shepp_logan\nfrom forward_projection import generate_sinogram\nimport matplotlib.pyplot as plt\n\nphantom = generate_shepp_logan(256)\nclean_sino, angles = generate_sinogram(phantom, 180)\n\nplt.figure(figsize=(8,5))\nplt.imshow(clean_sino, cmap="hot", aspect="auto")\nplt.title("Radon Transform (Sinogram)")\nplt.xlabel("Angle (theta)")\nplt.ylabel("Detector Offset (s)")\nplt.colorbar(label="Line Integral p(s, theta)")\nplt.show()'),
    ('md', '## 2. Noise Modeling (Poisson Statistics)\n\nX-ray photon detection is a **Poisson process**. Noise does *not* exist directly in the Radon transform domain; it exists in the raw photon counts. Therefore, our code (`src/noise_model.py`) converts the clean sinogram back to photon intensity before adding noise.\n\n$$ I_{expected} = I_0 e^{-p(s, \\theta)} $$\n$$ I_{measured} \\sim \\text{Poisson}(I_{expected}) $$\n\nFor a Poisson distribution, the variance equals the mean:\n$$ \\text{Var}(I) = E[I] = I $$\n\nThis creates the fundamental dose-noise tradeoff. The relative noise (Standard Deviation / Mean) is:\n$$ \\frac{\\sigma}{\\mu} = \\frac{\\sqrt{I}}{I} = \\frac{1}{\\sqrt{I}} $$\n\nIf we reduce the dose $I_0$ by a factor of 4, the noise doubles! After generating $I_{measured}$, we log-transform it back into a noisy sinogram:\n$$ p_{noisy} = -\\ln\\left(\\frac{I_{measured}}{I_0}\\right) $$'),
    ('code', '# Example: Adding Poisson Noise\nfrom noise_model import add_poisson_noise\n\nnoisy_sino, noisy_intensity = add_poisson_noise(clean_sino, I0=1e4)\n\nplt.figure(figsize=(8,5))\nplt.imshow(noisy_sino, cmap="hot", aspect="auto")\nplt.title("Noisy Sinogram (Low Dose I_0 = 10^4)")\nplt.colorbar(label="Noisy Line Integral")\nplt.show()'),
    ('md', '## 3. Filtered Back-Projection (Reconstruction)\n\nFBP is based on the **Fourier Slice Theorem**, which states that the 1D Fourier Transform of a projection at angle $\\theta$ is a slice of the 2D Fourier Transform of the original object at angle $\\theta$.\n\nIn our code (`src/fbp.py`), reconstruction is a two-step process:\n\n### Step 3a: Filtering\nTo correct for the non-uniform sampling density in polar coordinates, we must multiply the frequency domain by a ramp filter $|\\omega|$. To control noise, we multiply by an apodization window $H(\\omega)$ (e.g., Hamming, Cosine).\n\n$$ p_{filtered}(\\theta, s) = \\mathcal{F}^{-1} \\{ |\\omega| \\cdot H(\\omega) \\cdot \\mathcal{F}\\{ p(\\theta, s) \\} \\} $$\n\n### Step 3b: Back-Projection\nWe smear the filtered projections back across the image grid. For each pixel $(x,y)$, we find the corresponding detector offset $s$ and sum over all angles:\n\n$$ \\mu(x,y) = \\int_0^\\pi p_{filtered}(\\theta, x\\cos\\theta + y\\sin\\theta) d\\theta $$'),
    ('code', '# Example: Reconstructing the Noisy Sinogram using FBP\nfrom fbp import reconstruct_fbp\n\nreconstruction = reconstruct_fbp(noisy_sino, angles, filter_name="ram-lak")\n\nplt.figure(figsize=(6,6))\nplt.imshow(reconstruction, cmap="gray", vmin=0, vmax=0.05)\nplt.title("FBP Reconstruction (Ram-Lak Filter)")\nplt.axis("off")\nplt.show()'),
    ('md', '## 4. System Performance Evaluation\n\nOur system characterizes the scanner using three clinical metrics.\n\n### 4a. Spatial Resolution (MTF)\nThe Modulation Transfer Function (MTF) measures how well the system preserves spatial frequencies. We extract the Edge Spread Function (ESF), take the derivative to get the Line Spread Function (LSF), and take the Fourier transform:\n\n$$ \\text{LSF}(x) = \\frac{d}{dx} \\text{ESF}(x) $$\n$$ \\text{MTF}(f) = |\\mathcal{F}\\{\\text{LSF}(x)\\}| $$\n\n### 4b. Noise Texture (NPS)\nThe Noise Power Spectrum (NPS) tells us *where* the noise energy sits in the frequency domain. It is heavily influenced by the reconstruction filter.\n\n$$ \\text{NPS}(u,v) = \\frac{\\Delta x \\Delta y}{N_x N_y} \\langle |\\mathcal{F}\\{\\text{ROI}_{noise}\\}|^2 \\rangle $$\n\n### 4c. Object Detectability (CNR)\nThe Contrast-to-Noise Ratio (CNR) uses the **Rose Criterion** ($CNR \\geq 3$) to determine if a human observer can detect a tumor.\n\n$$ \\text{CNR} = \\frac{|\\mu_{insert} - \\mu_{background}|}{\\sigma_{background}} $$')
]

create_notebook('00_pipeline_theory.ipynb', theory_cells)
