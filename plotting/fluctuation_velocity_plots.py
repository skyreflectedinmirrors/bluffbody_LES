import matplotlib.pyplot as plt

from read_simulation_data import read_simulation_data
from common import get_default_parsing_args, UserOptions, Plot


class FluctuationVelocityPlot(Plot):
    base_sim_name = 'axialDeficitPlot_{point}'
    base_exp_name = 'fluctuationVelocity'

    def __init__(self, opts, velocity_component, num_points):
        super(FluctuationVelocityPlot, self).__init__(
            FluctuationVelocityPlot.base_sim_name, opts,
            exp_name=FluctuationVelocityPlot.base_exp_name,
            sharey=num_points)
        self.velocity_component = velocity_component

    def figname(self):
        return '{vc}_prime_rms.pdf'.format(
            vc=self.velocity_component)

    def xlim(self):
        if self.velocity_component == 'y':
            return (0, 1.0)
        else:
            return (0, 0.75)

    def ylim(self):
        return (-1.5, 1.5)

    def sim_name(self, point='', **kwargs):
        return FluctuationVelocityPlot.base_sim_name.format(point=point)

    def title(self, point='', **kwargs):
        p = point.split('p')
        p = float(p[0]) + float(''.join(p[1])) / 10**len(p[1])
        return r"$x/D = {}$".format(p)

    def figsize(self):
        return (20, 8)

    def process(self, caseno, case, **kwargs):
        # read baseline averaged data
        baseline = read_simulation_data(case, self.sim_name(**kwargs), self.opts,
                                        velocity_component=self.velocity_component)
        # read fluctuation data
        fluct = read_simulation_data(case, self.sim_name(**kwargs), self.opts,
                                     velocity_component=self.velocity_component,
                                     collection_type='fluct',
                                     collection_method='rms',
                                     baseline=baseline)
        # normalize / convert simulation data
        fluct.normalize(self.opts.reacting)
        # and plot
        pltargs = {}
        if not kwargs.get('hold', True):
            pltargs['label'] = self.label('U' + self.velocity_component + "'", case)
        plt.plot(fluct[:, 1], fluct[:, 0], color=self.opts.color(
            caseno), **pltargs)


def plot(opts):
    points = ['0p375', '0p95', '1p53', '3p75', '9p4']
    for vc in opts.velocity_component:
        fvp = FluctuationVelocityPlot(opts, vc, len(points))
        for i, point in enumerate(points):
            fvp.plot(point=point, velocity_component=vc, hold=i)
        fvp.finalize(point=point)


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
