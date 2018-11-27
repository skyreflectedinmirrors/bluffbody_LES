from os.path import join as pjoin

import matplotlib.pyplot as plt

from read_simulation_data import read_simulation_data
from read_experimental_data import read_experimental_data
from common import get_default_parsing_args, UserOptions

graph_name = 'meanAxialVelocity'


def process(caseno, case, opts):
    if not caseno:
        expdata = read_experimental_data(graph_name, opts.reacting)
    simdata = read_simulation_data(case, graph_name, opts)
    # normalize / convert simulation data
    simdata.normalize(opts.reacting)

    if not caseno:
        plt.scatter(expdata[:, 0], expdata[:, 1], label=expdata.name,
                    color=opts.color(caseno, exp=True))

    label = simdata.name
    if opts.ncases > 1:
        label += ' ({})'.format(case)

    plt.plot(simdata[:, 0], simdata[:, 1], label=label, color=opts.color(caseno))
    if not caseno:
        plt.xlabel(expdata.columns[0])
        plt.ylabel(expdata.columns[1])


def plot(opts):
    for caseno, casename in enumerate(opts.cases):
        opts.make_dir(casename)
        process(caseno, casename, opts)

    plt.xlim((None, 10.))
    plt.legend(loc=0)
    plt.savefig(pjoin(opts.out_path, 'mean_axial_velocity.pdf'))
    plt.close()


if __name__ == '__main__':
    parser = get_default_parsing_args(
        'mean_axial_velocity.py',
        'plots the time-averaged, normalized axial velocity '
        'along the centerline of the Volvo bluff-body experiment, as compared '
        'to experimental data')
    args = parser.parse_args()

    opts = UserOptions(args.caselist, args.reacting, args.start_time, args.end_time,
                       args.base_path, args.out_path)
    plot(opts)
