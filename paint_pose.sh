#!/bin/bash
#SBATCH --job-name=first_try      # Job name
#SBATCH --mail-type=ALL              # Mail events (NONE, BEGIN, END, FAIL, ALL)
#SBATCH --mail-user=3gmichels@gmail.com    # Where to send mail	
#SBATCH --nodes=1                    # Run all processes on a single node	
#SBATCH --ntasks=1                   # Run a single task		
#SBATCH --cpus-per-task=1            # Number of CPU cores per task
#SBATCH --mem=1gb                    # Job memory request
#SBATCH --time=00:05:00              # Time limit hrs:min:sec
#SBATCH --gres=gpu:1				 # Amount of GPUs

module purge
module load python/3.7.7

CUDA_VISIBLE_DEVICES="0" python3 -m openpifpaf.video_pose --batch-size 1 --jaad_batch_size 1 \
--checkpoint outputs/resnet50block5-pif-paf-crm-edge401-190526-203030.pkl.epoch006 \
--jaad_train "singletxt_pre_train_1s" --jaad_val "singletxt_val_1s" --jaad_pre_train "singletxt_pre_train_1s"