"""
An OpenFOAM converter that generates best-fit Sutherland transport data
from Chemkin/Cantera-type transport models

Nicholas Curtis

04/16/2018

Requires:
    - python installation, with:
        - Cantera
        - numpy
        - scipy
        - matplotlib (if -plot is supplied)
    The required versions should be reasonably agnost
"""

from __future__ import division
from argparse import ArgumentParser
from string import Template

import cantera as ct
import numpy as np
from scipy.optimize import curve_fit
try:
    from matplotlib import pyplot as plt
    import matplotlib.cm as cm
except ImportError:
    plt = None


def sutherland(T, As, Ts):
    # define the sutherland transport function
    return As * np.sqrt(T) / (1 + Ts / T)


def jacobian(T, As, Ts):
    # define analytical jacobian, because it's easy and why not
    jac = np.zeros((T.size, 2))

    # entry 0, dSutherland / dAs = sqrt(T) / (1 + Ts / T)
    jac[:, 0] = np.sqrt(T) / (1 + Ts / T)

    # entry 1, dSutherland / dTs
    jac[:, 1] = -As * np.power(T, 1.5) / np.power(Ts + T, 2)

    return jac


def main(gas, Tmin, Tmax, num=1000, plot=False, num_species_per_plot=4):
    # get temperature range
    Trange = np.linspace(Tmin, Tmax, num=num)

    # calculate viscosities
    visc = np.zeros((num, gas.n_species))
    for i, T in enumerate(Trange):
        # pressure irrelevant, but required to set state
        gas.TP = T, ct.one_atm
        visc[i, :] = gas.species_viscosities

    coeffs = np.zeros((2, gas.n_species))
    # calculate best fits
    for i, species in enumerate(gas.species_names):
        (As, Ts), fit = curve_fit(sutherland, Trange, visc[:, i], jac=jacobian)
        coeffs[:, i] = As, Ts

    if plot:
        # plot fits, if desired
        if plt is None:
            raise Exception('matplotlib not installed.')
        colors = cm.viridis(np.linspace(0, 1, num_species_per_plot))
        linewheel = ['-', '--', '-.', ':']
        for i in range(0, gas.n_species, num_species_per_plot):
            spec_inds = np.arange(i, np.minimum(i + num_species_per_plot,
                                                gas.n_species))
            sl_max = -1
            sl_min = 1e100
            for i_spec, spec_i in enumerate(spec_inds):
                plt.scatter(Trange, visc[:, spec_i], c=colors[i_spec],
                            label=gas.species_names[spec_i])
                plt.plot(Trange, sutherland(Trange, *coeffs[:, spec_i]),
                         linestyle=linewheel[i_spec], color='k',
                         label=gas.species_names[spec_i] + ' (fit)')
                sl_max = np.maximum(np.max(sutherland(Trange, *coeffs[:, spec_i])),
                                    sl_max)
                sl_min = np.minimum(np.min(sutherland(Trange, *coeffs[:, spec_i])),
                                    sl_min)
            plt.legend(loc=0, ncol=2)
            plt.ylabel('Species Viscosity (Pa-s)')
            plt.xlabel('Temperature (K)')
            plt.gca().set_yscale('log')
            plt.gca().set_xscale('log')
            ymax = np.maximum(np.max(visc[:, spec_inds]), sl_max)
            ymin = np.minimum(np.min(visc[:, spec_inds]), sl_min)
            plt.gca().set_ylim((0.95 * ymin, 1.05 * ymax))
            plt.tight_layout()
            plt.show()

    template = Template("""
       ${name}
       {
            transport
            {
                As              ${As};
                Ts              ${Ts};
            }
       }""")
    for i, spec in enumerate(gas.species_names):
        print(template.substitute(name=spec, As=coeffs[0, i], Ts=coeffs[1, i]))


if __name__ == '__main__':
    parser = ArgumentParser(
        'foamSutherlandTransport.py: A utility to convert species transport '
        'parameters in chemkin/cantera format to Sutherland transport for OpenFOAM.')
    parser.add_argument('-m', '--mech',
                        help='The Cantera mechanism to fit transport parameters for.'
                             'If you have a Chemkin-format mechanism, see: '
                             'http://www.cantera.org/docs/sphinx/html/cti/input-files.html#converting-ck-format-files',  # noqa
                        type=str)
    parser.add_argument('-t', '--transport_model',
                        help='The transport model to use with the mechanism. '
                             'This has no effect on the fitting process, but is '
                             'necessary to load the correct gas phase from the '
                             'mechanism (i.e., so transport data is defined).')
    parser.add_argument('-Tmin', '--minimum_temperature',
                        help='The minimum temperature to uses in transport model '
                             "fitting. If not specified, defaults to the mechanism's"
                             'minimum temperature.',
                        default=None,
                        type=float,
                        required=False)
    parser.add_argument('-Tmax', '--maximum_temperature',
                        help='The maximum temperature to uses in transport model '
                             "fitting. If not specified, defaults to the mechanism's"
                             'maximum temperature.',
                        default=None,
                        type=float,
                        required=False)
    parser.add_argument('-np', '--npoints',
                        help='The number of points in the temperature range to '
                             'test.',
                        default=1000,
                        type=int,
                        required=False)
    parser.add_argument('-s', '--species',
                        help='A comma separated list, or regular-expression of '
                             'species in the mechanism to fit transport parameters '
                             'for.  If not specified, all species in the mechanism'
                             'will be fit.',
                        default=None,
                        required=False)
    parser.add_argument('-p', '--plot',
                        help='Plot curve fits.',
                        required=False,
                        action='store_true',
                        default=False)
    args = parser.parse_args()
    gas = ct.Solution(args.mech)
    if gas.transport_model == 'Transport':
        try:
            gas.transport_model = args.transport_model
        except ct.CanteraError:
            raise Exception('Mechanism {} does not have the specified transport '
                            'model {}.'.format(args.mech, args.transport_model))
    Tmin = gas.min_temp if args.minimum_temperature is None else \
        args.minimum_temperature
    Tmax = gas.max_temp if args.maximum_temperature is None else \
        args.maximum_temperature

    if args.species:
        # limit species
        try:
            # comma separated list
            species = [x.strip() for x in args.species.split(',')]
        except TypeError:
            import re
            re_match = re.compile(args.species)
            species = [x for x in gas.species_names if re_match.search(x)]
        gas = gas[species]

    main(gas, Tmin, Tmax, args.npoints, args.plot)
