#!/bin/bash
#SBATCH --job-name=vocab-train
#SBATCH --output=output.txt
#SBATCH --error=output.txt
#SBATCH --time=0-23:0
#SBATCH --partition=dgxh100
#SBATCH -G1

source /data/ai_club/team_3_2024-25/team3-env-finetune/bin/activate
python test_finetune.py
