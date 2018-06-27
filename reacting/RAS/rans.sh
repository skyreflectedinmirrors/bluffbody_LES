#!/bin/bash
#SBATCH --partition=serial           # run on requeue partition
#SBATCH --time=7-00:00:00            # Job should run for no more than 12 hours
#SBATCH --nodes=2                    # one node
#SBATCH --ntasks=48                  # 24 cores
#SBATCH --exclude=cn[01-136,325-328] # only run on haswell
#SBATCH --mem 100G                   # up to 100 gigs
#SBATCH -o rans_reacting.out
#SBATCH -e rans_reacting.err
#SBATCH --mail-type=END              # mail
#SBATCH --mail-user=nicholas.curtis@uconn.edu
#SBATCH --dependency=singleton
#SBATCH --signal=USR1@60

export IPM_NESTED_REGIONS=1
export JOB="reactingFoamIPM -parallel"
srun -N$SLURM_JOB_NUM_NODES -n$SLURM_NTASKS --mpi=openmpi $JOB
