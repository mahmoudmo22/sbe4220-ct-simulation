#!/bin/bash
set -e

echo "Starting Git history rewrite..."

# Create a new branch so we don't accidentally destroy your current work
# If the branch already exists, we delete it first to start fresh
git checkout main
git branch -D rewrite-authors 2>/dev/null || true
git checkout -b rewrite-authors

# Soft reset to the commit right BEFORE all the code was added (c81d5bb)
# This keeps all your files exactly as they are right now, but erases the commit history after c81d5bb
git reset --soft c81d5bb

# Unstage all files
git reset HEAD

# ---------------------------------------------------------
# 1. Mahmoud Bahaa's Commits
# ---------------------------------------------------------
git add src/fbp.py
git commit -m "feat: implement Filtered Back-Projection (FBP) algorithm" --author="Mahmoud Bahaa <2odabahaa@gmail.com>"

# ---------------------------------------------------------
# 2. Rashed Mamdouh's Commits
# ---------------------------------------------------------
git add src/mtf.py src/nps.py src/cnr.py src/metrics.py
git commit -m "feat: implement quantitative evaluation metrics (MTF, NPS, CNR)" --author="Rashed Mamdouh <rashed.mahmoud02@eng-st.cu.edu.eg>"

# ---------------------------------------------------------
# 3. Mohamed Ashraf's Commits
# ---------------------------------------------------------
git add src/noise_model.py
git commit -m "feat: implement Poisson noise modeling and dose simulation" --author="Mohamed Ashraf <medo.ashroof@gmail.com>"

# ---------------------------------------------------------
# 4. Ammar Yasser's Commits
# ---------------------------------------------------------
git add notebooks/experiment_2_filters.ipynb notebooks/experiment_3_dose.ipynb notebooks/experiment_4_mtf_projections.ipynb notebooks/experiment_5_system_characterization.ipynb results/
git commit -m "feat: implement experimental analysis notebooks and generate results" --author="Ammar Yasser <ammargoda03@gmail.com>"

# ---------------------------------------------------------
# 5. Mahmoud Mohamed's Commits (Your work)
# ---------------------------------------------------------
git add src/phantom.py src/forward_projection.py src/utils.py notebooks/experiment_1_baseline.ipynb notebooks/00_pipeline_theory.ipynb
git commit -m "feat: implement phantom generation, forward projection, and baseline notebooks" --author="Mahmoud Mohamed <mahmoud.soliman00@eng-st.cu.edu.eg>"

# ---------------------------------------------------------
# 6. Final Project Wrap-up (Your work)
# ---------------------------------------------------------
git add app.py generate_notebooks.py generate_theory_notebook.py requirements.txt README.md .gitignore documentation/ src/__init__.py rewrite_authors.sh
git commit -m "feat: build Streamlit UI, documentation, and finalize project structure" --author="Mahmoud Mohamed <mahmoud.soliman00@eng-st.cu.edu.eg>"

echo ""
echo "✅ History rewritten successfully on branch 'rewrite-authors'!"
git log --oneline --author-date-order -n 8
