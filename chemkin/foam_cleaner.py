from argparse import ArgumentParser
import re
import cantera as ct
import numpy as np


def main(thermo, model, cantera_model):

    # load the cantera solution
    gas = ct.Solution(cantera_model)

    print('Santizing the THERMO file.')
    # comment out all species that exist in the thermo database that \
    # aren't in the model
    reglist = [re.compile('^[ -]\\d\\.\\d+E[+-]\\d+'), re.compile('^\\s*!'),
               re.compile(r'^\s*\n\s*$'), re.compile(r'^( )+'),
               re.compile(r'^\s*THERMO'), re.compile(r'^\s*END')]

    with open(thermo) as file:
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

    suffix = thermo[thermo.rindex('.'):]
    with open('{}_clean{}'.format(
            thermo[:thermo.index(suffix)], suffix), 'w') as file:
        file.writelines(lines)

    # next check the chemkin model
    if any(isinstance(rxn, ct.PlogReaction) for rxn in gas.reactions()):
        print('Converting PLOG reactions to rate at 1 ATM')
    else:
        return 0

    # open model
    with open(model) as file:
        lines = file.readlines()

    plog_reg = re.compile(r'^\s*plog\s*/', re.IGNORECASE)
    param_reg = re.compile(r'(-?(?:\d+)?\.?(?:\d+)?(?:E[+-]?\d+)?)\s+'
                           r'(-?(?:\d+)?\.?(?:\d+)?(?:E[+-]?\d+)?)\s+'
                           r'(-?(?:\d+)?\.?(?:\d+)?(?:E[+-]?\d+)?)\s*$')
    plog_param_reg = re.compile(r'(-?(?:\d+)?\.?(?:\d+)?(?:E[+-]?\d+)?)\s+'
                                r'(-?(?:\d+)?\.?(?:\d+)?(?:E[+-]?\d+)?)\s+'
                                r'(-?(?:\d+)?\.?(?:\d+)?(?:E[+-]?\d+)?)\s+'
                                r'(-?(?:\d+)?\.?(?:\d+)?(?:E[+-]?\d+)?)\s*/')
    dup_reg = re.compile(r'^\s*dup\s*$', re.IGNORECASE)

    do_plog = False
    found_one_atm = False
    out_lines = lines[:]
    for i, line in enumerate(lines):
        if not do_plog and plog_reg.search(line):
            # store reaction to overwrite
            do_plog = i - 1
            if dup_reg.search(lines[do_plog]):
                raise Exception('Bad duplicate specification on line {}.  Should be '
                                'at the end of the reaction.'.format(i + 1))

        if do_plog:
            if not plog_reg.search(line):
                # end of reaction
                if not found_one_atm:
                    raise Exception('One ATM plog rate not found!')

                # now, replace the lines
                for j in range(do_plog + 1, i):
                    out_lines[j] = None

                # and replace the parameters in the regular reaction string
                rxn = lines[do_plog]
                match = param_reg.search(rxn)
                old_params = rxn[match.span()[0]:match.span()[1]].strip()
                one_atm = plog_param_reg.search(lines[found_one_atm])
                one_atm_params = ' '.join(one_atm.groups()[1:])
                rxn = rxn[:match.span()[0]]
                print("""
Updating PLOG rxn:
    Reaction string: {},
    Old parameters: {},
    One atm parameters: {}
      -> From line: {}
""".format(rxn, old_params, one_atm_params, lines[found_one_atm]))

                # replace
                new_rxn = (rxn.strip() + ' ' + one_atm_params).strip() + '\n'
                out_lines[do_plog] = new_rxn

                # turn off plog check
                do_plog = False
                continue

            match = plog_param_reg.search(line)
            assert match, 'Plog reaction rate could not be parsed: {}'.format(
                line)

            # get pressure
            pressure = float(match.group(1))
            if np.isclose(pressure, 1.0):
                found_one_atm = i

    out_lines = [x for x in out_lines if x is not None]
    suffix = model[model.rindex('.'):]
    with open('{}_clean{}'.format(
            model[:model.index(suffix)], suffix), 'w') as file:
        file.writelines(out_lines)


if __name__ == '__main__':
    parser = ArgumentParser('foam_cleaner.py -- Chemkin file sanitation for '
                            'the OpenFOAM parser chemkinToFoam')
    parser.add_argument('-th', '--thermo',
                        type=str,
                        help='The CHEMKIN format thermo file to fixup.',
                        required=True)
    parser.add_argument('-m', '--model',
                        type=str,
                        help='The CHEMKIN format kinetic model file to fixup.',
                        required=True)
    parser.add_argument('-c', '--cantera_model',
                        type=str,
                        help='The conveted Cantera format kinetic model '
                             'corresponding to the given CHEMKIN files.',
                        required=True)

    args = parser.parse_args()
    main(args.thermo, args.model, args.cantera_model)
