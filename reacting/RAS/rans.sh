#!/bin/bash
#SBATCH --partition=parallel         # run on requeue partition
#SBATCH --time=06:00:00              # Job should run for no more than 12 hours
#SBATCH --nodes=2                    # one node
#SBATCH --ntasks=48                  # 24 cores
#SBATCH --exclude=cn[01-136,325-328] # only run on haswell
#SBATCH --mem 100G                   # up to 100 gigs
#SBATCH -o rans_reacting.out
#SBATCH -e rans_reacting.err
#SBATCH --mail-type=END              # mail
#SBATCH --mail-user=nicholas.curtis@uconn.edu
#SBATCH --dependency=singleton


mpirun reactingFoam -case . -parallel
