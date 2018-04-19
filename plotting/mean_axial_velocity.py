from __future__ import division, print_function

from argparse import ArgumentParser

import matplotlib.pyplot as plt

from read_simulation_data import read_simulation_data
from read_experimental_data import read_experimental_data

graph_name = 'meanAxialVelocity'
D = 40 / 1000  # mm
Ubulk = 16.6   # m/s
offset = -100.0 / 1000  # mm


def plot(case, reacting, t_start=0, t_end=-1):
    expdata = read_experimental_data(graph_name, args.reacting)
    simdata = read_simulation_data(case, graph_name, reacting, t_start, t_end,
                                   averaging_type='simps')
    # normalize / convert simulation data
    simdata[:, 0] -= offset
    simdata[:, 0] /= -D
    simdata[:, 1] /= -Ubulk

    plt.plot(expdata[:, 0], expdata[:, 1], label=expdata.name)
    plt.plot(simdata[:, 0], simdata[:, 1], label=simdata.name)
    plt.xlabel(expdata.columns[0])
    plt.ylabel(expdata.columns[1])
    plt.legend(loc=0)
    plt.savefig('test.png')


if __name__ == '__main__':
    parser = ArgumentParser(
        'mean_axial_velocity.py: plots the time-averaged, normalized axial velocity '
        'along the centerline of the Volvo bluff-body experiment, as compared '
        'to experimental data')
    parser.add_argument('-r', '--reacting',
                        help='Plot the reacting-flow data.',
                        action='store_true',
                        dest='reacting',
                        default=False,
                        required=False)
    parser.add_argument('-n', '--non_reacting',
                        help='Plot the reacting-flow data.',
                        action='store_false',
                        dest='reacting',
                        required=False)
    parser.add_argument('-c', '--case',
                        help='The simulation to plot',
                        choices=['LES', 'RAS'],
                        required=True)
    parser.add_argument('-t_start', '--start_time',
                        help='The start time for simulation averaging in seconds.',
                        required=False,
                        type=float,
                        default=0)
    parser.add_argument('-t_end', '--end_time',
                        help='The end time for simulation averaging in seconds.',
                        required=False,
                        type=float,
                        default=-1)
    args = parser.parse_args()

    plot(args.case, args.reacting, args.start_time, args.end_time)
