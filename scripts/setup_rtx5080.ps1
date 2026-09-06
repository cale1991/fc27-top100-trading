$ErrorActionPreference = "Stop"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    py -m pip install uv
}
uv venv --python 3.12
.\.venv\Scripts\Activate.ps1
uv pip install -e ".[features,ml,dev]"
$torchIndex = if ($env:TORCH_INDEX_URL) { $env:TORCH_INDEX_URL } else { "https://download.pytorch.org/whl/cu128" }
uv pip install torch --index-url $torchIndex
python -c "import torch; print('torch', torch.__version__); print('cuda', torch.cuda.is_available()); print('gpu', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE')"
