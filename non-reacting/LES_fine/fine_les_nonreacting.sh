#!/bin/bash
#SBATCH --partition=parallel	     # run on parallel partition
#SBATCH --time=6:00:00               # Job should run for no more than 12 hours
#SBATCH --nodes=2                    # two nodes
#SBATCH --ntasks=48                  # 48 cores
#SBATCH --exclude=cn[01-136,325-328] # only run on haswell
#SBATCH --mem 100G                   # up to 100 gigs
#SBATCH -o les_nonreacting.out
#SBATCH -e les_nonreacting.out
#SBATCH --dependency=singleton

mpirun reactingFoam -case . -parallel -noFunctionObjects
