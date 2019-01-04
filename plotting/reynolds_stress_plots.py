import matplotlib.pyplot as plt
import numpy as np

from read_simulation_data import read_simulation_data, integration_averager
from common import get_default_parsing_args, UserOptions, Plot, dataset


class ReynoldsStressPlot(Plot):
    base_sim_name = 'axialDeficitPlot_{point}'
    base_exp_name = 'reynoldsStress'

    def __init__(self, opts, num_points):
        super(ReynoldsStressPlot, self).__init__(
            ReynoldsStressPlot.base_sim_name, opts,
            exp_name=ReynoldsStressPlot.base_exp_name,
            sharey=num_points)
        self.velocity_components = ['x', 'y']

    def figname(self):
        return 'reynolds_stress.pdf'

    def xlim(self):
        return (-0.25, 0.25)

    def ylim(self):
        return (-1.5, 1.5)

    def sim_name(self, point='', **kwargs):
        return ReynoldsStressPlot.base_sim_name.format(point=point)

    def title(self, point='', **kwargs):
        p = point.split('p')
        p = float(p[0]) + float(''.join(p[1:])) / 100.
        return "x/D = {}".format(p)

    def figsize(self):
        return (20, 8)

    def process(self, caseno, case, **kwargs):
        out = None
        for vc in self.velocity_components:
            # read baseline averaged data
            baseline = read_simulation_data(case, self.sim_name(**kwargs), self.opts,
                                            velocity_component=vc)
            # read fluctuation data
            fluct = read_simulation_data(case, self.sim_name(**kwargs), self.opts,
                                         velocity_component=vc,
                                         collection_type='fluct',
                                         collection_method='fluct',
                                         baseline=baseline)

            # multiply the velocity fluctuations
            if out is None:
                out = fluct
            else:
                out = fluct * out

        vals = np.zeros((out.data.shape[1:]))
        # copy in yaxis
        vals[:, 0] = out.data[0, :, 0]
        # time average
        for var in range(1, out.data.shape[2]):
            vals[:, var] = integration_averager()(out.data[:, :, var], out.time)

        to_plot = dataset(out.columns[:], vals, out.name,
                          is_simulation=out.is_simulation, time=out.time)

        # normalize / convert simulation data twice (for the squared velocity)
        to_plot.normalize(self.opts.reacting, velocity_power=2.0)

        # and plot
        pltargs = {}
        if not kwargs.get('hold', True):
            pltargs['label'] = self.label(r'Simulation', case)
        plt.plot(to_plot[:, 1], to_plot[:, 0], color=self.opts.color(caseno),
                 **pltargs)


def plot(opts):
    points = ['0p375', '0p95', '1p53', '3p75', '9p4']
    fvp = ReynoldsStressPlot(opts, len(points))
    for i, point in enumerate(points):
        fvp.plot(point=point, hold=i)
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
