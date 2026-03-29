#!/usr/bin/env bash
set -euo pipefail
cd /mnt/c/Users/abinr/RadVerify
source /mnt/c/Users/abinr/RadVerify/.venv_wsl/bin/activate
export RADVERIFY_API_KEY="${RADVERIFY_API_KEY:-radverify_secret_key}"
export LD_LIBRARY_PATH=/usr/lib/wsl/lib:/usr/local/cuda/targets/x86_64-linux/lib:/lib/x86_64-linux-gnu:${LD_LIBRARY_PATH:-}
exec uvicorn api_server:app --host 0.0.0.0 --port 8000