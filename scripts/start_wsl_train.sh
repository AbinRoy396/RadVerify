#!/usr/bin/env bash
set -euo pipefail
cd /mnt/c/Users/abinr/RadVerify
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
logfile="logs/train_${ts}.log"
nohup env RADVERIFY_DATASET_PATH=data/structure_dataset RADVERIFY_EPOCHS=20 RADVERIFY_BATCH_SIZE=16 /home/abinr/radverify_venv/bin/python -u train_model.py > "$logfile" 2>&1 < /dev/null &
pid=$!
echo "PID:$pid LOG:$logfile"
