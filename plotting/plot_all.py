
from common import get_default_parsing_args, UserOptions
from fluctuation_velocity_plots import plot as fplot
from mean_axial_velocity import plot as mplot
from axial_deficit_plots import plot as aplot
from reynolds_stress_plots import plot as rplot

plotters = [fplot, mplot, aplot, rplot]

if __name__ == '__main__':
    parser = get_default_parsing_args(
            'plot_all.py',
            'Generates all plots for the given case.')

    args = parser.parse_args()
    for plot in plotters:
        opts = UserOptions(args.caselist, args.reacting, args.start_time,
                           args.end_time, args.base_path, args.out_path)
        plot(opts)
