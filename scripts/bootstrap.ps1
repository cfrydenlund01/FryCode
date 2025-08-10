param([switch]$GPU)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
if (!(Test-Path ".venv")) { py -3 -m venv .venv }
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip wheel setuptools
pip install -r requirements.txt
if ($GPU) {
  Write-Host "For PyTorch + CUDA: install a matching torch wheel from pytorch.org/get-started/locally/"
  Write-Host "For llama-cpp with CUDA: pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir --config-settings=cmake.args=-DGGML_CUDA=on"
}
if (!(Test-Path ".env.example")) { New-Item ".env.example" -ItemType File | Out-Null }
pre-commit install
