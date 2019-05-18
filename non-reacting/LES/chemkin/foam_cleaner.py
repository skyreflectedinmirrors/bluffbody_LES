import re
import cantera as ct

# comment out all species that exist in the thermo database that aren't in the model
reglist = [re.compile('^[ -]\\d\\.\\d+E[+-]\\d+'), re.compile('^\\s*!'),
           re.compile(r'^\s*\n\s*$'), re.compile(r'^( )+'),
           re.compile(r'^\s*THERMO'), re.compile(r'^\s*END')]

gas = ct.Solution('skeletal.cti')

with open('skeletal_therm.dat') as file:
    lines = file.readlines()

do_comment = 0
for i, line in enumerate(lines):
    if not any(r.search(line) for r in reglist) and line.strip():
        name = line[:line.index(' ')]
        if name not in gas.species_names:
            assert not do_comment
            do_comment = 4
    if do_comment:
        lines[i] = '!' + lines[i]
        do_comment -= 1

with open('skeletal_therm_clean.dat', 'w') as file:
    file.writelines(lines)
