NUM_GPU=3
export N_CTX=8000
export MODEL_PATH="/data/ai_club/llms/mixtral-8x7b-instruct-v0.1.Q6_K.gguf"

srun -G${NUM_GPU} --pty bash -c "source /data/ai_club/team_3_2024-25/team3-env-py312-glibc/bin/activate; \
    hostname; \
    jupyter notebook \
        --ServerApp.root_dir=$(pwd) \
        --ServerApp.password='' \
        --ServerApp.open_browser=False \
        --ServerApp.allow_origin='*' \
        --ServerApp.allow_remote_access=True \
        --ServerApp.port=14321 \
        --ServerApp.ip='*'
"
