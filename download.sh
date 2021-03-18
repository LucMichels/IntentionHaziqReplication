#!/bin/bash

pwd; hostname; date

echo "Evaluating Haziq's model"

module purge
module load gcc/8.4.0-cuda python/3.7.7
source /home/michels/venvs/download/bin/activate

deactivate

date