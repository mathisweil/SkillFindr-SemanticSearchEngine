## 🐍 Conda Environment Setup

To ensure compatibility and reproducibility, it is recommended to use a dedicated conda environment.

### ✅ Create and Activate Environment

```bash
# Create a new environment with Python 3.12
conda create -n skillfindr python=3.12

# Activate the environment
conda activate skillfindr

# Install dependencies from requirements.txt
pip install -r requirements.txt
```

### 💡 Notes
- Make sure `conda` is installed (via [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/)).
- You can deactivate the environment with `conda deactivate`.
- Environment variables are loaded from a `.env` file, which must be defined before running the scraper or API.
