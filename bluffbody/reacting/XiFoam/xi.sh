#!/bin/bash
#SBATCH --partition=general_requeue  # run on requeue partition
#SBATCH --time=12:00:00              # Job should run for no more than 12 hours
#SBATCH --nodes=1                    # one node
#SBATCH --ntasks=24                  # 24 cores
#SBATCH --exclude=cn[65-69,71-136,325-343,345-353,355-358,360-364,369-398,400-401],gpu[07-10] # only run on haswell
#SBATCH --mem 100G                   # up to 100 gigs
#SBATCH -o xi.out
#SBATCH -e xi.err
#SBATCH --mail-type=END              # mail
#SBATCH --mail-user=nicholas.curtis@uconn.edu
#SBATCH --dependency=singleton
#SBATCH --signal=SIGTERM@60


mpirun XiFoam -case . -parallel
