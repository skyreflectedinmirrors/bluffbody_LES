from common import get_default_parsing_args, UserOptions, Plot


class AxialDeficitPlot(Plot):
    graph_name = 'axialDeficitPlot_{point}'

    def __init__(self, opts, velocity_component, num_points):
        super(AxialDeficitPlot, self).__init__(
            AxialDeficitPlot.graph_name, opts,
            sharey=num_points)
        self.velocity_component = velocity_component

    def figname(self):
        return 'axial_deficit_plot_{}.pdf'.format(self.velocity_component)

    def xlim(self):
        if self.velocity_component == 'y':
            return (-1, 1)
        else:
            return (-0.5, 2)

    def ylim(self):
        return (-1.5, 1.5)

    def simulation_column_map(self):
        return (1, 0)

    def title(self, point='', **kwargs):
        p = point.split('p')
        p = float(p[0]) + float(''.join(p[1:])) / 100.
        return "x/D = {}".format(p)

    def sim_name(self, point='', **kwargs):
        return AxialDeficitPlot.graph_name.format(point=point)

    def figsize(self):
        return (20, 8)


def plot(opts):
    for vc in opts.velocity_component:
        points = ['0p375', '0p95', '1p53', '3p75', '9p4']
        adp = AxialDeficitPlot(opts, vc, len(points))
        for i, point in enumerate(points):
            adp.plot(point=point, velocity_component=vc, hold=i)
        adp.finalize(point=point)


if __name__ == '__main__':
    parser = get_default_parsing_args(
        'axial_deficit_plot.py',
        'plots the time-averaged, normalized axial and tangential velocity '
        'at different axial slices along the centerline of the Volvo bluff-body '
        'experiment, as compared to experimental data')
    parser.add_argument('-v', '--velocity_component',
                        choices=['z', 'y', 'both'],
                        help='The velocity component to plot',
                        default='both',
                        required=False)
    args = parser.parse_args()

    opts = UserOptions(args.caselist, args.reacting, args.start_time, args.end_time,
                       args.base_path, args.out_path, args.velocity_component)
    plot(opts)
