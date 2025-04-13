#!/bin/bash

TTS_PORT=8221
IMG_GEN_PORT=8222
LLM_PORT=8223

echo Starting...

# srun -G1 --pty bash -c "source /data/ai_club/team_3_2024-25/team3-env-py312-glibc/bin/activate; \
srun -G2 -N1 --pty bash -c "source /data/ai_club/team_3_2024-25/team3-env-finetune/bin/activate; \
    python ./tts.py $TTS_PORT & \
    python ./img_gen.py $IMG_GEN_PORT & \
    python ./llm.py $LLM_PORT & \
    wait \
"
