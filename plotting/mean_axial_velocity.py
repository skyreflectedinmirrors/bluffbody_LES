from os.path import join as pjoin

import matplotlib.pyplot as plt

from read_simulation_data import read_simulation_data
from read_experimental_data import read_experimental_data
from common import get_default_parsing_args, make_dir

graph_name = 'meanAxialVelocity'


def plot(case, reacting, t_start=0, t_end=-1):
    make_dir(case)
    expdata = read_experimental_data(graph_name, reacting)
    simdata = read_simulation_data(case, graph_name, reacting, t_start, t_end)
    # normalize / convert simulation data
    simdata.normalize(reacting)

    plt.scatter(expdata[:, 0], expdata[:, 1], label=expdata.name, color='r')
    plt.plot(simdata[:, 0], simdata[:, 1], label=simdata.name)
    plt.xlabel(expdata.columns[0])
    plt.ylabel(expdata.columns[1])
    plt.legend(loc=0)
    plt.savefig(pjoin(case, 'mean_axial_velocity.pdf'))


if __name__ == '__main__':
    parser = get_default_parsing_args(
        'mean_axial_velocity.py',
        'plots the time-averaged, normalized axial velocity '
        'along the centerline of the Volvo bluff-body experiment, as compared '
        'to experimental data')
    args = parser.parse_args()

    plot(args.case, args.reacting, args.start_time, args.end_time)
