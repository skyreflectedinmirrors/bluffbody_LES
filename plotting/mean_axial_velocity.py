from common import get_default_parsing_args, UserOptions, Plot

graph_name = 'meanAxialVelocity'


class MeanAxialVelocityPlot(Plot):
    graph_name = 'meanAxialVelocity'

    def __init__(self, opts):
        super(MeanAxialVelocityPlot, self).__init__(
            MeanAxialVelocityPlot.graph_name, opts,
            label_names={'U': 'Normalized Centerline Axial Velocity'})

    def figname(self):
        return 'mean_axial_velocity.pdf'

    def xlim(self):
        return (0, 10)

    def exp_column_map(self):
        return (0, 1)

    def title(self):
        return "Centerline Mean Axial Velocity Profile"


def plot(opts):
    MeanAxialVelocityPlot(opts).plot()


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
