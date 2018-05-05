#!/bin/bash
#SBATCH --partition=general_requeue  # run on requeue partition
#SBATCH --time=12:00:00              # Job should run for no more than 12 hours
#SBATCH --nodes=1                    # one node
#SBATCH --ntasks=24                  # 24 cores
#SBATCH --exclude=cn[01-136,325-328] # only run on haswell
#SBATCH --mem 100G                   # up to 100 gigs
#SBATCH -o rans_nonreacting.out
#SBATCH -e rans_nonreacting.err
#SBATCH --mail-type=END              # mail
#SBATCH --mail-user=nicholas.curtis@uconn.edu
#SBATCH --dependency=singleton


mpirun reactingFoam -case /home/njc07003/OpenFOAM/njc07003-5.x/run/volvo_flygmotor_AB/non-reacting/RAS -parallel
