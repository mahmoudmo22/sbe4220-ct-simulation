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

exp2_cells = [
    ('md', '# Experiment 2: Effect of Reconstruction Filters\n\nThis experiment evaluates the resolution-noise tradeoff across different FBP filters: Ram-Lak, Shepp-Logan, Cosine, and Hamming.'),
    ('code', 'import os, sys\nsys.path.append(os.path.abspath("../src"))\nimport numpy as np\nimport matplotlib.pyplot as plt\nfrom phantom import generate_qa_phantom\nfrom forward_projection import generate_sinogram\nfrom fbp import reconstruct_fbp, AVAILABLE_FILTERS\nfrom mtf import compute_mtf_from_reconstruction\nfrom nps import compute_nps\nfrom utils import display_images_grid, plot_mtf_curves, plot_nps_curves\nos.makedirs("../results", exist_ok=True)'),
    ('md', '## 1. Generate QA Phantom and Sinogram'),
    ('code', 'phantom, metadata = generate_qa_phantom(size=256)\nnum_angles = 360\nsinogram, angles = generate_sinogram(phantom, num_angles)'),
    ('md', '## 2. Reconstruct with all filters'),
    ('code', 'recons = {}\nfor filt in AVAILABLE_FILTERS:\n    print(f"Reconstructing with {filt}...")\n    recons[filt] = reconstruct_fbp(sinogram, angles, filter_name=filt)'),
    ('md', '## 3. Visual Comparison'),
    ('code', 'display_images_grid([recons[f] for f in AVAILABLE_FILTERS], titles=AVAILABLE_FILTERS, ncols=2, save_path="../results/exp2_filters_visual.png")'),
    ('md', '## 4. MTF (Spatial Resolution) and NPS (Noise Texture) Analysis'),
    ('code', 'mtf_results = {}\nnps_results = {}\n\nfor filt in AVAILABLE_FILTERS:\n    recon = recons[filt]\n    # MTF\n    freq_mtf, mtf_vals = compute_mtf_from_reconstruction(recon, method="edge")\n    mtf_results[filt] = (freq_mtf, mtf_vals)\n    # NPS\n    center_norm = metadata["uniform_roi"]["center_norm"]\n    freq_nps, nps_vals, _, _ = compute_nps(recon, roi_size=32, num_rois=8, center=(128,128))\n    nps_results[filt] = (freq_nps, nps_vals)'),
    ('code', 'plot_mtf_curves(mtf_results, title="MTF by Filter", save_path="../results/exp2_mtf.png")\nplot_nps_curves(nps_results, title="NPS by Filter", save_path="../results/exp2_nps.png")')
]

exp3_cells = [
    ('md', '# Experiment 3: Dose vs. Image Quality\n\nSimulating Poisson noise at different incident photon counts ($I_0$) to analyze SNR, NPS, and object detectability (CNR).'),
    ('code', 'import os, sys\nsys.path.append(os.path.abspath("../src"))\nimport numpy as np\nimport matplotlib.pyplot as plt\nfrom phantom import generate_qa_phantom\nfrom forward_projection import generate_sinogram\nfrom noise_model import generate_dose_series\nfrom fbp import reconstruct_fbp\nfrom nps import compute_nps\nfrom cnr import cnr_vs_dose, compute_cnr_from_qa_phantom\nfrom utils import display_images_grid, plot_nps_curves, plot_metric_vs_parameter'),
    ('md', '## 1. Simulate Clean Sinogram and Noisy Dose Series'),
    ('code', 'phantom, metadata = generate_qa_phantom(size=256)\nclean_sino, angles = generate_sinogram(phantom, 360)\ndose_levels = [1e6, 1e5, 1e4, 1e3]\ndose_series = generate_dose_series(clean_sino, dose_levels=dose_levels)'),
    ('md', '## 2. Reconstruct each dose level (Ram-Lak filter)'),
    ('code', 'recons = {}\nfor dose in dose_levels:\n    noisy_sino = dose_series[dose]["noisy_sinogram"]\n    recons[dose] = reconstruct_fbp(noisy_sino, angles, filter_name="ram-lak")'),
    ('md', '## 3. Visual Comparison'),
    ('code', 'titles = [f"I_0 = {d:.0e}" for d in dose_levels]\nimages = [recons[d] for d in dose_levels]\ndisplay_images_grid(images, titles=titles, ncols=2, save_path="../results/exp3_dose_visual.png")'),
    ('md', '## 4. CNR and NPS Analysis'),
    ('code', 'doses_arr, cnr_arr, details = cnr_vs_dose(recons, metadata, insert_index=0)\nplot_metric_vs_parameter(doses_arr, cnr_arr, "Incident Photons (I0)", "CNR", title="CNR vs Dose", log_x=True, save_path="../results/exp3_cnr.png")'),
    ('code', 'nps_results = {}\nfor dose in dose_levels:\n    freq_nps, nps_vals, _, _ = compute_nps(recons[dose], roi_size=32, num_rois=8, center=(128,128))\n    nps_results[f"I_0 = {dose:.0e}"] = (freq_nps, nps_vals)\nplot_nps_curves(nps_results, title="NPS vs Dose", log_scale=True, save_path="../results/exp3_nps.png")')
]

exp4_cells = [
    ('md', '# Experiment 4: Spatial Resolution vs Angular Sampling\n\nQuantifying how angular undersampling degrades MTF.'),
    ('code', 'import os, sys\nsys.path.append(os.path.abspath("../src"))\nimport numpy as np\nimport matplotlib.pyplot as plt\nfrom phantom import generate_qa_phantom\nfrom forward_projection import generate_sinogram\nfrom fbp import reconstruct_fbp\nfrom mtf import compute_mtf_from_reconstruction\nfrom utils import plot_mtf_curves, display_images_grid'),
    ('md', '## 1. Reconstruct at different projection counts'),
    ('code', 'phantom, metadata = generate_qa_phantom(size=256)\nangles_list = [360, 180, 90, 45]\nrecons = {}\nmtf_results = {}\n\nfor num_angles in angles_list:\n    sino, angles = generate_sinogram(phantom, num_angles)\n    recon = reconstruct_fbp(sino, angles, filter_name="ram-lak")\n    recons[num_angles] = recon\n    freq, mtf_vals = compute_mtf_from_reconstruction(recon, method="edge")\n    mtf_results[f"{num_angles} Angles"] = (freq, mtf_vals)'),
    ('md', '## 2. Plot Results'),
    ('code', 'display_images_grid([recons[a] for a in angles_list], titles=[f"{a} Angles" for a in angles_list], ncols=2, save_path="../results/exp4_visual.png")\nplot_mtf_curves(mtf_results, title="MTF vs Angular Sampling", save_path="../results/exp4_mtf.png")')
]

exp5_cells = [
    ('md', '# Experiment 5: System Characterization\n\nComparing 4 distinct operating points simultaneously.'),
    ('code', 'import os, sys\nsys.path.append(os.path.abspath("../src"))\nimport numpy as np\nimport matplotlib.pyplot as plt\nfrom phantom import generate_qa_phantom\nfrom forward_projection import generate_sinogram\nfrom noise_model import add_poisson_noise\nfrom fbp import reconstruct_fbp\nfrom mtf import compute_mtf_from_reconstruction\nfrom nps import compute_nps\nfrom cnr import compute_cnr_from_qa_phantom\nfrom metrics import compute_rmse\nfrom utils import display_images_grid, plot_mtf_curves, plot_nps_curves'),
    ('md', '## 1. Setup Operating Points'),
    ('code', 'phantom, metadata = generate_qa_phantom(256)\n# 1. High Dose, High Angle, Sharp (Baseline)\nsino_360, ang_360 = generate_sinogram(phantom, 360)\nnoisy_highdose, _ = add_poisson_noise(sino_360, 1e6)\nrecon_1 = reconstruct_fbp(noisy_highdose, ang_360, "ram-lak")\n\n# 2. High Dose, Low Angle, Sharp\nsino_90, ang_90 = generate_sinogram(phantom, 90)\nnoisy_90, _ = add_poisson_noise(sino_90, 1e6)\nrecon_2 = reconstruct_fbp(noisy_90, ang_90, "ram-lak")\n\n# 3. Low Dose, High Angle, Sharp\nnoisy_lowdose, _ = add_poisson_noise(sino_360, 1e4)\nrecon_3 = reconstruct_fbp(noisy_lowdose, ang_360, "ram-lak")\n\n# 4. High Dose, High Angle, Smooth\nrecon_4 = reconstruct_fbp(noisy_highdose, ang_360, "hamming")\n\nrecons = [recon_1, recon_2, recon_3, recon_4]\ntitles = ["1. Baseline (1e6, 360, RamLak)", "2. Low Angles (1e6, 90, RamLak)", "3. Low Dose (1e4, 360, RamLak)", "4. Smooth (1e6, 360, Hamming)"]'),
    ('md', '## 2. Visual Comparison'),
    ('code', 'display_images_grid(recons, titles=titles, ncols=2, save_path="../results/exp5_visual.png")'),
    ('md', '## 3. Extract Metrics'),
    ('code', 'mtf_res, nps_res = {}, {}\nfor r, t in zip(recons, titles):\n    f_mtf, m_vals = compute_mtf_from_reconstruction(r, method="edge")\n    mtf_res[t] = (f_mtf, m_vals)\n    f_nps, n_vals, _, _ = compute_nps(r, roi_size=32, num_rois=8, center=(128,128))\n    nps_res[t] = (f_nps, n_vals)\n    cnr, _ = compute_cnr_from_qa_phantom(r, metadata)\n    rmse = compute_rmse(r, phantom)\n    print(f"{t}: CNR={cnr:.2f}, RMSE={rmse:.4f}")'),
    ('md', '## 4. Plot MTF and NPS'),
    ('code', 'plot_mtf_curves(mtf_res, save_path="../results/exp5_mtf.png")\nplot_nps_curves(nps_res, log_scale=True, save_path="../results/exp5_nps.png")')
]

create_notebook('experiment_2_filters.ipynb', exp2_cells)
create_notebook('experiment_3_dose.ipynb', exp3_cells)
create_notebook('experiment_4_mtf_projections.ipynb', exp4_cells)
create_notebook('experiment_5_system_characterization.ipynb', exp5_cells)
