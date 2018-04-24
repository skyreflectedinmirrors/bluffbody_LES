import matplotlib.pyplot as plt

from read_simulation_data import read_simulation_data
from read_experimental_data import read_experimental_data
from common import get_default_parsing_args, make_dir

graph_name = 'axialDeficitPlot'


def plot(case, reacting, t_start=0, t_end=-1, velocity_component='both'):
    if velocity_component == 'both':
        velocity_component = ['z', 'y']
    else:
        velocity_component = [velocity_component]

    make_dir(case)
    for point in ['0p375', '0p95', '1p53', '3p75', '9p4']:
        for vc in velocity_component:
            expdata = read_experimental_data(graph_name, args.reacting,
                                             velocity_component=vc, point=point)
            simdata = read_simulation_data(case, graph_name, reacting, t_start,
                                           t_end)
            # normalize / convert simulation data
            simdata.normalize(reacting)

            plt.plot(expdata[:, 1], expdata[:, 0], label=expdata.name)
            plt.plot(simdata[:, 1], simdata[:, 0], label=simdata.name)
            plt.xlabel(expdata.columns[0])
            plt.ylabel(expdata.columns[1])
            plt.legend(loc=0)
            plt.savefig('axial_deficit_plot_{point}.pdf'.format(point=point))
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
