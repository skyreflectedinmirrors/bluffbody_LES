from __future__ import print_function

# based onhttps://www.cantera.org/docs/sphinx/html/cython/examples/onedim_flamespeed_sensitivity.html
# and https://www.cantera.org/docs/sphinx/html/cython/examples/onedim_flame_fixed_T.html

import cantera as ct

# Simulation parameters
p = ct.one_atm  # pressure [Pa]
Tin = 300.0  # unburned gas temperature [K]
phi = 0.62
reactants = 'CH4:0.45, O2:1.0, N2:3.76'

width = 0.03  # m

# IdealGasMix object used to compute mixture properties
gas = ct.Solution('gri30.xml', 'gri30_mix')
gas.TP = Tin, p
gas.set_equivalence_ratio(phi, 'CH4', 'O2:1.0, N2:3.76')

# Flame object
f = ct.FreeFlame(gas, width=width)
f.set_refine_criteria(ratio=3, slope=0.07, curve=0.14)

f.solve(loglevel=1, auto=True)
print('\nmixture-averaged flamespeed = {:7f} m/s\n'.format(f.u[0]))

print('\n\n switching to multicomponent transport...\n\n')
f.transport_model = 'Multi'

f.set_refine_criteria(ratio=3.0, slope=0.1, curve=0.2)
f.solve(loglevel=1, auto=True)

print('\nmulticomponent flamespeed = {:7f} m/s\n'.format(f.u[0]))
