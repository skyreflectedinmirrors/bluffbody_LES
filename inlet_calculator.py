from __future__ import division, print_function
import argparse
import cantera as ct
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
parser.add_argument('-g', '--gas',
                    default='gri30.cti',
                    type=str)
parser.add_argument('-f', '--fuel',
                    default='CH4',
                    type=str,
                    help='The name of the fuel molecule to use in the mechanism.')
parser.add_argument('-p', '--phase',
                    default='',
                    type=str)
parser.set_defaults(reacting=True)
args = parser.parse_args()
reacting = args.reacting

# calculate inlet conditions for b.c.'s'
gas = ct.Solution(args.gas, args.phase)
gas.transport_model = 'Multi'


# from MVP recommendations
# T0 = 288 k
# P0 = 100 kPa
T0 = 288  # K
P0 = 1e5  # kpa
mdot = 0.2079  # kg / s

# U_bulk = 16.6 if not reacting else 17.2

# dimensions
D = 40 / 1000  # mm
width = 2 * D
height = 3 * D
area = width * height

# equivalence ratio -- MVP2
# NOTE: 06/13 raised equivalence ratio to 0.82 to avoid repeated weak-flame /
# strong-flame cycles
phi = 1.0 if reacting else 0

# iterate to find static conditions
print('Non-reacting' if not reacting else 'Reacting')


def T_static(U_bulk):
    return T0 - U_bulk**2 / (2. * gas.cp)


def gamma():
    return gas.cp / gas.cv


def P_static(Ts):
    return P0 / ((T0 / Ts) ** (gamma() / (gamma() - 1)))


U_bulk = 16.6 if not reacting else 17.2

print('U_bulk: {} m/s'.format(U_bulk))

Ts = T_static(U_bulk)
Ps = P_static(Ts)

print('Static temperature: {} K'.format(Ts))
print('Static pressure: {} kPa'.format(Ps))

# set state
gas.TP = Ts, Ps
# and equivalence ratio
gas.set_equivalence_ratio(phi, args.fuel, 'O2:1.0, N2:3.76')

print('Inlet mass fractions:')
print(gas[[args.fuel, 'O2', 'N2']].mass_fraction_dict())

print('Inlet density: {} (kg/m^3)'.format(gas.density_mass))

# get velocity
print('Inlet gamma: {}'.format(gamma()))

a = np.sqrt(gamma() * ct.gas_constant * gas.T / gas.mean_molecular_weight)
print('Speed of sound: {} m/s'.format(a))
print('Inlet mach: ', U_bulk / a)

# Reynolds #
print('Re: {}'.format((gas.density_mass * U_bulk * D) / gas.viscosity))
print('mdot: {} (kg/s)'.format(gas.density_mass * U_bulk * area))


print(gas())
