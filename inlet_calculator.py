from __future__ import division, print_function
import argparse
import cantera as ct
from scipy.optimize import fsolve
import numpy as np

parser = argparse.ArgumentParser('inlet_calculator -- print properties at inlet!')
parser.add_argument('-r', '--reacting',
                    dest='reacting',
                    action='store_true',
                    required=False)
parser.add_argument('-n', '--non_reacting',
                    dest='reacting',
                    action='store_false',
                    required=False)
parser.set_defaults(reacting=True)
reacting = parser.parse_args().reacting

# calculate inlet conditions for b.c.'s'
gas = ct.Solution('chemkin/ucsd.cti')


# from MVP recommendations
# T0 = 288 k
# P0 = 100 kPa
# mdot = 0.2079 kg/s
T0 = 288  # K
P0 = 1e5  # kpa
# from the experimental data _this_ appears to be fixed, rather than the mass flow rate
U_bulk = 16.6 if not reacting else 17.2

# mass_flow_rate = 0.2079  # kg/s

# dimensions
D = 40 / 1000  # mm
width = 2 * D
height = 3 * D
area = width * height

# equivalence ratio -- MVP2
phi = 0.62 if reacting else 0

# iterate to find static conditions
print('Non-reacting' if not reacting else 'Reacting')


def static_deviation(xs):
    """
    Takes a test static temperature / pressure & computes the deviation
    w.r.t. the specified stagnation conditions
    """

    # extract
    Ts, Ps = xs
    # set gas state
    gas.TP = Ts, Ps
    gas.set_equivalence_ratio(phi, 'C3H8', 'O2:1.0, N2:3.76')

    # now we have the density
    U_test = U_bulk

    # specific heat ratio
    gamma = gas.cp / gas.cv

    # calculate speed of sound & mach #
    a = np.sqrt(gamma * Ps / gas.density)
    M = U_test / a

    # https://www.grc.nasa.gov/www/k-12/airplane/isentrop.html

    # now we can convert from T -> T0
    T0_test = Ts * (1 + ((gamma - 1) / 2.) * M * M)

    # use isentropic relation to get P0
    P0_test = Ps * (1 + ((gamma - 1) / 2.) * M * M) ** (gamma / (gamma - 1))

    # and return difference
    return np.array([T0 - T0_test, P0 - P0_test])


Ts, Ps = fsolve(static_deviation, np.array([0.95 * T0, 0.95 * P0]))

print('Static temperature: {} K'.format(Ts))
print('Static pressure: {} kPa'.format(Ps))

# set state
gas.TP = Ts, Ps
# and equivalence ratio
gas.set_equivalence_ratio(phi, 'C3H8', 'O2:1.0, N2:3.76')

print('Inlet mass fractions:')
print(gas[['C3H8', 'O2', 'N2']].mass_fraction_dict())

print('Inlet gamma: {}'.format(gas.cp / gas.cv))
# get velocity

# mass flow rate from MVP2
mass_flow_rate = (gas.density * area) * U_bulk
print('Inlet mass flow rate: {} kg/s'.format(mass_flow_rate))

a = np.sqrt((gas.cp / gas.cv) * ct.gas_constant * gas.T)
print('Inlet mach: ', U_bulk / a)

# Reynolds #
print('Re: {}'.format((gas.density * U_bulk * D) / gas.viscosity))
