import matplotlib.pyplot as plt

from read_simulation_data import read_simulation_data
from read_experimental_data import read_experimental_data
from common import get_default_parsing_args, make_dir
from os.path import join as pjoin

sim_name = 'axialDeficitPlot_{point}'
exp_name = 'fluctuationVelocity'


def plot(case, reacting, t_start=0, t_end=-1, velocity_component='both'):
    if velocity_component == 'both':
        velocity_component = ['z', 'y']
    else:
        velocity_component = [velocity_component]

    make_dir(case)
    for point in ['0p375', '0p95', '1p53', '3p75', '9p4']:
        for vc in velocity_component:
            name = sim_name.format(point=point)
            # first read experimental data
            expdata = read_experimental_data(exp_name, reacting,
                                             velocity_component=vc, point=point)
            # read baseline averaged data
            baseline = read_simulation_data(case, name, reacting, t_start,
                                            t_end, velocity_component=vc)
            # read fluctuation data
            fluct = read_simulation_data(case, name, reacting, t_start,
                                         t_end, velocity_component=vc,
                                         collection_type='fluct',
                                         collection_method='rms',
                                         baseline=baseline)
            # normalize / convert simulation data
            fluct.normalize(reacting)

            plt.scatter(expdata[:, 1], expdata[:, 0], label=expdata.name,
                        color='r')
            plt.plot(fluct[:, 1], fluct[:, 0], label=fluct.name)
            plt.xlabel(expdata.columns[1])
            plt.ylabel(expdata.columns[0])
            plt.gca().set_xlim([-1, 1] if velocity_component == 'y' else
                               [-1, 2])
            plt.legend(loc=0)
            plt.savefig(pjoin(case,
                        '{vc}_prime_rms_{point}.pdf'.format(
                            vc=vc, point=point)))
            plt.close()


if __name__ == '__main__':
    parser = get_default_parsing_args(
        'mean_axial_velocity.py',
        'plots the time-averaged, normalized axial velocity '
        'along the centerline of the Volvo bluff-body experiment, as compared '
        'to experimental data')
    parser.add_argument('-v', '--velocity_component',
                        choices=['z', 'y', 'both'],
                        help='The velocity component to plot',
                        default='both',
                        required=False)
    args = parser.parse_args()

    plot(args.case, args.reacting, args.start_time, args.end_time,
         args.velocity_component)