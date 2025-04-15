# srun -G1 --partition dgx --pty bash 
# source /data/ai_club/team_3_2024-25/team3-env-dgx/bin/activate
# python test_llama_dgx.py

# srun -G1 --partition dgx --pty bash -c "source /data/ai_club/team_3_2024-25/team3-env-dgx/bin/activate; python test_llama_dgx.py"

import transformers
import torch

