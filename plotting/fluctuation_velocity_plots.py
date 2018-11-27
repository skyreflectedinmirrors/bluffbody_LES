import matplotlib.pyplot as plt

from read_simulation_data import read_simulation_data
from common import get_default_parsing_args, UserOptions, Plot


class FluctuationVelocityPlot(Plot):
    sim_name = 'axialDeficitPlot_{point}'
    exp_name = 'fluctuationVelocity'

    def __init__(self, opts, point, velocity_component):
        super(FluctuationVelocityPlot, self).__init__(
            FluctuationVelocityPlot.sim_name.format(point=point), opts,
            read_exp_kwargs={'point': point,
                             'velocity_component': velocity_component},
            exp_name=FluctuationVelocityPlot.exp_name)
        self.point = point
        self.velocity_component = velocity_component

    def figname(self):
        return '{vc}_prime_rms_{point}.pdf'.format(
            vc=self.velocity_component,
            point=self.point)

    def xlim(self):
        return (0, 2)

    def ylim(self):
        return (-1.5, 1.5)

    def process(self, caseno, case, **kwargs):
        # read baseline averaged data
        baseline = read_simulation_data(case, self.sim_name, self.opts,
                                        velocity_component=self.velocity_component)
        # read fluctuation data
        fluct = read_simulation_data(case, self.sim_name, self.opts,
                                     velocity_component=self.velocity_component,
                                     collection_type='fluct',
                                     collection_method='rms',
                                     baseline=baseline)
        # normalize / convert simulation data
        fluct.normalize(self.opts.reacting)
        # and plot
        label = self.label(fluct.name, case)
        plt.plot(fluct[:, 1], fluct[:, 0], label=label, color=self.opts.color(
            caseno))


def plot(opts):
    for point in ['0p375', '0p95', '1p53', '3p75', '9p4']:
        for vc in opts.velocity_component:
            fvp = FluctuationVelocityPlot(opts, point, vc)
            fvp.plot()


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
