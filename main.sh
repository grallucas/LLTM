#!/bin/bash

source /data/ai_club/team_3_2024-25/team3-env-py312-glibc/bin/activate

NODE=dh-node8

python ./app/main.py 8001 ${NODE}:8221,${NODE}:8222

# IDEA
# This file will eventually be run on the BACKEND server (digital ocean, someone's laptop, mgmt node, etc).
# It will tunnel into Rosie if needed and
# 1) start the tts & img models + get the node+ports,
# 2) start the backend "locally" on the server (so the server has the img+node adresses as global inputs)

# also have quick restart like before