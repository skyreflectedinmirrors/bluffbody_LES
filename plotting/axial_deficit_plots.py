from common import get_default_parsing_args, UserOptions, Plot


class AxialDeficitPlot(Plot):
    graph_name = 'axialDeficitPlot_{point}'

    def __init__(self, opts, point, velocity_component):
        super(AxialDeficitPlot, self).__init__(
            AxialDeficitPlot.graph_name.format(point=point), opts,
            read_exp_kwargs={'point': point,
                             'velocity_component': velocity_component},
            multiplot=True)
        self.point = point
        self.velocity_component = velocity_component

    def figname(self):
        return 'axial_deficit_plot_{vc}_{point}.pdf'.format(
            vc=self.velocity_component,
            point=self.point)

    def xlim(self):
        return (-0.5, 2)

    def ylim(self):
        return (-1.5, 1.5)

    def simulation_column_map(self):
        return (1, 0)

    def figsize(self):
        return (3, 9)

    def title(self):
        return "x/D = {}".format(self.point)


def plot(opts):
    for point in ['0p375', '0p95', '1p53', '3p75', '9p4']:
        for vc in opts.velocity_component:
            adp = AxialDeficitPlot(opts, point, vc)
            adp.plot(point=point, velocity_component=vc)


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

    opts = UserOptions(args.caselist, args.reacting, args.start_time, args.end_time,
                       args.base_path, args.out_path, args.velocity_component)
    plot(opts)
