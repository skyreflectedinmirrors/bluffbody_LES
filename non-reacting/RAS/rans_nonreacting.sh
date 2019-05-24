#!/bin/bash
#SBATCH --partition=general_requeue  # run on requeue partition
#SBATCH --time=12:00:00              # Job should run for no more than 12 hours
#SBATCH --nodes=1                    # one node
#SBATCH --ntasks=24                  # 24 cores
#SBATCH --exclude=cn[65-69,71-136,325-343,345-353,355-358,360-364,369-398,400-401],gpu[07-10] # only run on haswell
#SBATCH --mem 100G                   # up to 100 gigs
#SBATCH -o rans_nonreacting.out
#SBATCH -e rans_nonreacting.err
#SBATCH --mail-type=END              # mail
#SBATCH --mail-user=nicholas.curtis@uconn.edu
#SBATCH --dependency=singleton


mpirun reactingFoam -case . -parallel
