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
        self.velocity_components = ['z', 'y']

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
        return (20, 6)

    def process(self, caseno, case, **kwargs):
        # read baseline averaged data
        Ux = read_simulation_data(case, self.sim_name(**kwargs), self.opts,
                                  velocity_component='z',
                                  collection_method='none')
        Uy = read_simulation_data(case, self.sim_name(**kwargs), self.opts,
                                  velocity_component='y',
                                  collection_method='none')
        # do a dummy normalization to make sure the signs are correct
        Ux.normalize(self.opts.reacting, velocity_power=0.0)
        Uy.normalize(self.opts.reacting, velocity_power=0.0)

        # calculate avg(uv)
        Uxy = Ux * Uy
        Uxy_mean = integration_averager()(Uxy.data[:, :, 1], Uxy.time)

        # calculate avg(u) * avg(v)
        Ux_Uy_mean = integration_averager()(Ux.data[:, :, 1], Ux.time) * \
            integration_averager()(Uy.data[:, :, 1], Uy.time)

        # mean(u'v') = mean(uv) - mean(u)mean(v)
        vals = np.zeros(Ux.data.shape[1:])
        vals[:, 0] = Ux.data[0, :, 0]
        vals[:, 1] = Uxy_mean - Ux_Uy_mean

        # normalize / convert simulation data twice (for the squared velocity)
        from common import dimensions
        dim = dimensions(self.opts.reacting)
        vals[:, 1] /= (dim.Ubulk * dim.Ubulk)

        to_plot = dataset(Ux.columns[:], vals, Ux.name,
                          is_simulation=Ux.is_simulation, time=Ux.time)
        # and plot
        plt.plot(to_plot[:, 1], to_plot[:, 0],
                 **self.get_plotargs(Ux.name, caseno, case,
                                     hold=kwargs.get('hold', None)))


def plot(opts):
    points = ['0p375', '0p95', '1p53', '3p75', '9p4']
    fvp = ReynoldsStressPlot(opts, len(points))
    for i, point in enumerate(points):
        fvp.plot(point=point, hold=i)
    fvp.finalize(point=point)


if __name__ == '__main__':
    parser = get_default_parsing_args(
        'reynolds_stress_plots.py',
        'plots the mean Renyolds Stresses at different axial slices '
        'along the centerline of the Volvo bluff-body experiment, as compared '
        'to experimental data')
    args = parser.parse_args()
    opts = UserOptions(args.caselist, args.reacting, args.start_time, args.end_time,
                       args.base_path, args.out_path)

    plot(opts)
