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

import cantera as ct
import numpy as np
try:
    from matplotlib import pyplot as plt
    import matplotlib.cm as cm
except ImportError:
    plt = None


def plotter(Trange, Trange_extended, arr, arr2, name, ns, num_species_per_plot):
    # plot fits, if desired
    if plt is None:
        raise Exception('matplotlib not installed.')
    colors = cm.viridis(np.linspace(0, 1, num_species_per_plot))
    linewheel = ['-', '--', '-.', ':']
    for i in range(0, ns, num_species_per_plot):
        spec_inds = np.arange(i, np.minimum(i + num_species_per_plot, ns))
        sl_max = -1
        sl_min = 1e100
        for i_spec, spec_i in enumerate(spec_inds):
            plt.scatter(Trange, arr[:, spec_i],
                        c=colors[i_spec], label=gas.species_names[spec_i])
            plt.plot(Trange_extended, arr2[:, spec_i],
                     linestyle=linewheel[i_spec], color='k',
                     label=gas.species_names[spec_i] + ' (extended)')
            sl_max = np.maximum(np.max(arr[:, spec_i]), sl_max)
            sl_min = np.minimum(np.min(arr2[:, spec_i]), sl_min)
        plt.legend(loc=0, ncol=2)
        plt.ylabel(name)
        plt.xlabel('Temperature (K)')
        if sl_min > 0:
            plt.gca().set_yscale('log')
        plt.gca().set_xscale('log')
        plt.gca().set_ylim((0.95 * sl_min, 1.05 * sl_max))
        plt.tight_layout()
        plt.show()


def main(gas, Tmin, Tmax, num=1000, plot=False, num_species_per_plot=4):
    # get temperature range
    Trange = np.linspace(gas.min_temp, Tmax, num=num)
    Trange_extended = np.linspace(Tmin, Tmax, num=num)

    ns = len(gas.species_names)
    # calculate cp / h
    cp_extended = np.zeros((num, ns))
    cp = np.zeros((num, ns))

    h_extended = np.zeros((num, ns))
    h = np.zeros((num, ns))
    for i, T in enumerate(Trange):
        # pressure irrelevant, but required to set state
        T_ext = Trange_extended[i]
        for j, spec_name in enumerate(gas.species_names):
            thermo = gas.species(spec_name).thermo
            cp[i, j] = thermo.cp(T)
            h[i, j] = thermo.h(T)

            cp_extended[i, j] = thermo.cp(T_ext)
            h_extended[i, j] = thermo.h(T_ext)

    if plot:
        plotter(Trange, Trange_extended, cp, cp_extended, 'Specific Heat [J/kmolK]',
                ns, num_species_per_plot)
        plotter(Trange, Trange_extended, h, h_extended, 'Molar Enthalpy [J/kmol]',
                ns, num_species_per_plot)


if __name__ == '__main__':
    parser = ArgumentParser(
        'foamSutherlandTransport.py: A utility to convert species transport '
        'parameters in chemkin/cantera format to Sutherland transport for OpenFOAM.')
    parser.add_argument('-m', '--mech',
                        help='The Cantera mechanism to fit transport parameters for.'
                             'If you have a Chemkin-format mechanism, see: '
                             'http://www.cantera.org/docs/sphinx/html/cti/input-files.html#converting-ck-format-files',  # noqa
                        type=str)
    parser.add_argument('-Tmin', '--minimum_temperature',
                        help='The lower temperature bound to use in transport model '
                             "fitting. If not specified, defaults to the mechanism's"
                             'minimum temperature.',
                        default=None,
                        type=float)
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
    Tmin = args.minimum_temperature
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

    names = []
    for species in gas.species():
        if species.thermo.min_temp < Tmin:
            if args.species:
                print("Ignoring species {}, as it's minimum temperature is "
                      "lower than that requested".format(species.name))
            continue
        names.append(species.name)
    gas = gas[names]

    main(gas, Tmin, Tmax, args.npoints, args.plot)
