#!/bin/sh
PATH="$HOME/bin:$HOME/.local/bin:$PATH"
PATH="/home/pwilsil03/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin"

PYTHONPATH=":/home/pwilsil03/Insightzz/Tensorflow/models:/home/pwilsil03/Insightzz/Tensorflow/models/research/object_detection:/home/pwilsil03/Insightzz/Tensorflow/models/research:/home/pwilsil03/Insightzz/Tensorflow/models/research/slim:/home/pwilsil03/Insightzz/Tensorflow/models:/home/pwilsil03/Insightzz/Tensorflow/models/research/object_detection:/home/pwilsil03/Insightzz/Tensorflow/models/research:/home/pwilsil03/Insightzz/Tensorflow/models/research/slim"
export PATH=$PATH
export PYTHONPATH=$PYTHONPATH

nohup python3 /home/pwilsil03/Insightzz/code/Algorithms/ServiceCode/pwil_arduino_service_post.py > /dev/null &

