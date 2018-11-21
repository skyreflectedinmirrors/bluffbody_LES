
from common import get_default_parsing_args, get_cases
from fluctuation_velocity_plots import plot as fplot
from mean_axial_velocity import plot as mplot
from axial_deficit_plots import plot as aplot

plotters = [fplot, mplot, aplot]

if __name__ == '__main__':
    parser = get_default_parsing_args(
            'plot_all.py',
            'Generates all plots for the given case.')

    args = parser.parse_args()
    for plot in plotters:
        plot(get_cases(args.caselist, args.reacting, args.base_path),
             args.reacting, args.start_time, args.end_time,
             out_path=args.out_path)
