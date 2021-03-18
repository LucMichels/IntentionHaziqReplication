#!/bin/bash

pwd; hostname; date

echo "Downloading"

module purge
module load gcc/8.4.0-cuda python/3.7.7
source /home/michels/venvs/download/bin/activate
python download.py
deactivate

date