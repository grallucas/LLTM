#!/bin/bash

source /data/ai_club/team_3_2024-25/team3-env-py312-glibc/bin/activate

export PYTHONPATH="${PYTHONPATH}:${pwd}/models"
export PYTHONPATH="${PYTHONPATH}:${pwd}/app"

jupyter notebook \
    --ServerApp.root_dir=$(pwd) \
    --ServerApp.password='' \
    --ServerApp.open_browser=False \
    --ServerApp.allow_origin='*' \
    --ServerApp.allow_remote_access=True \
    --ServerApp.port=14321 \
    --ServerApp.ip='*'
