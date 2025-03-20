#!/bin/bash
#SBATCH --job-name=vocab-train
#SBATCH --output=output.txt
#SBATCH --error=output.txt
#SBATCH --time=0-23:0
#SBATCH --partition=dgx
#SBATCH -G1

source /data/ai_club/team_3_2024-25/team3-env-finetune/bin/activate
export IM_MODE="new-mask_old-ops"
python ../im_llm.py 200
