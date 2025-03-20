#!/bin/bash

TTS_PORT=8001
IMG_GEN_PORT=8002

srun -G1 --pty bash -c "source /data/ai_club/team_3_2024-25/team3-env-py312-glibc/bin/activate; \
    python ./tts.py $TTS_PORT & \
    python ./img_gen.py $IMG_GEN_PORT & \
    wait \
"
