# use this to start the LLTM frontend and backend

NUM_GPU=3
export N_CTX=8000
#export MODEL_PATH="/data/ai_club/llms/mixtral-8x7b-instruct-v0.1.Q6_K.gguf"
export MODEL_PATH="/data/ai_club/llms/qwen2.5-7b-instruct-q8_0-00001-of-00003.gguf"

srun -G${NUM_GPU} --pty bash -c "source /data/ai_club/team_3_2024-25/team3-env-py312-glibc/bin/activate; \
    python main.py    
"
