import matplotlib.pyplot as plt

from read_simulation_data import read_simulation_data
from read_experimental_data import read_experimental_data
from common import get_default_parsing_args, UserOptions
from os.path import join as pjoin

sim_name = 'axialDeficitPlot_{point}'
exp_name = 'fluctuationVelocity'


def process(caseno, case, point, velocity_component, opts):
    name = sim_name.format(point=point)
    # first read experimental data
    if not caseno:
        expdata = read_experimental_data(exp_name, opts.reacting,
                                         velocity_component=velocity_component,
                                         point=point)
    # read baseline averaged data
    baseline = read_simulation_data(case, name, opts,
                                    velocity_component=velocity_component)
    # read fluctuation data
    fluct = read_simulation_data(case, name, opts,
                                 velocity_component=velocity_component,
                                 collection_type='fluct',
                                 collection_method='rms',
                                 baseline=baseline)
    # normalize / convert simulation data
    fluct.normalize(opts.reacting)

    if not caseno:
        plt.scatter(expdata[:, 1], expdata[:, 0], label=expdata.name,
                    color=opts.color(caseno, exp=True))
    label = fluct.name
    if opts.ncases > 1:
        label += ' ({})'.format(case)
    plt.plot(fluct[:, 1], fluct[:, 0], label=label, color=opts.color(caseno))
    if not caseno:
        plt.xlabel(expdata.columns[1])
        plt.ylabel(expdata.columns[0])


def plot(opts):
    for point in ['0p375', '0p95', '1p53', '3p75', '9p4']:
        for vc in opts.velocity_component:
            for caseno, casename in enumerate(opts.cases):
                opts.make_dir(casename)
                process(caseno, casename, point, vc, opts)

            plt.gca().set_xlim([-1, 1] if vc == 'y' else
                               [-1, 2])
            plt.legend(loc=0)
            plt.savefig(pjoin(opts.out_path,
                        '{vc}_prime_rms_{point}.pdf'.format(
                            vc=vc, point=point)))
            plt.close()


if __name__ == '__main__':
    parser = get_default_parsing_args(
        'fluctuation_velocity_plots.py',
        'plots the RMS fluctuation velocity at different axial slices '
        'along the centerline of the Volvo bluff-body experiment, as compared '
        'to experimental data')
    parser.add_argument('-v', '--velocity_component',
                        choices=['z', 'y', 'both'],
                        help='The velocity component to plot',
                        default='both',
                        required=False)
    args = parser.parse_args()
    opts = UserOptions(args.caselist, args.reacting, args.start_time, args.end_time,
                       args.base_path, args.out_path, args.velocity_component)

    plot(opts)
