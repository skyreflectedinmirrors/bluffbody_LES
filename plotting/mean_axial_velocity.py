from os.path import join as pjoin

import matplotlib.pyplot as plt

from read_simulation_data import read_simulation_data
from read_experimental_data import read_experimental_data
from common import get_default_parsing_args, make_dir, get_cases

graph_name = 'meanAxialVelocity'


def process(caseno, case, reacting, t_start=0, t_end=-1, multiple_cases=False):
    make_dir(case)
    if not caseno:
        expdata = read_experimental_data(graph_name, reacting)
    simdata = read_simulation_data(case, graph_name, reacting, t_start, t_end)
    # normalize / convert simulation data
    simdata.normalize(reacting)

    if not caseno:
        plt.scatter(expdata[:, 0], expdata[:, 1], label=expdata.name, color='r')

    label = simdata.name
    if multiple_cases:
        label += ' ({})'.format(case)

    plt.plot(simdata[:, 0], simdata[:, 1], label=label)
    if not caseno:
        plt.xlabel(expdata.columns[0])
        plt.ylabel(expdata.columns[1])


def plot(case, reacting, t_start=0, t_end=-1, out_path=None):
    for caseno, casename in enumerate(case):
        process(caseno, casename, reacting, t_start, t_end, len(case) > 1)

    if out_path is None:
        out_path = case[0]

    plt.legend(loc=0)
    plt.savefig(pjoin(out_path, 'mean_axial_velocity.pdf'))
    plt.close()


if __name__ == '__main__':
    parser = get_default_parsing_args(
        'mean_axial_velocity.py',
        'plots the time-averaged, normalized axial velocity '
        'along the centerline of the Volvo bluff-body experiment, as compared '
        'to experimental data')
    args = parser.parse_args()

    plot(get_cases(args.caselist, args.reacting, args.base_path),
         args.reacting, args.start_time,
         args.end_time, out_path=args.out_path)
