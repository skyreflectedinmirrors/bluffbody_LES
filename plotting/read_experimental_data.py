import os
import re
import numpy as np

from common import dataset

script_dir = os.path.abspath(os.path.dirname(__file__))
non_reacting_path = os.path.join(script_dir, 'Experimental', 'Non-Reacting')
reacting_path = os.path.join(script_dir, 'Experimental', 'Reacting')


def read_file(filename, reacting=False):
    """
    Reads experimental from a file

    Parameters
    ----------
    file: str
        The filename to read
    reacting: bool [False]
        If true, look in the Reacting folder, else in the Non-Reacting folder

    Returns
    -------
    data: :class:`dataset`
        The resulting dataset
    """

    path = reacting_path if reacting else non_reacting_path
    data = np.loadtxt(os.path.join(path, filename), delimiter=',')[:, ::-1]

    # read column names
    comment = re.compile(r'^\s*#')
    column_names = re.compile(r'^\s*#\s*(.+)\s*,\s*(.+)\s*$')
    with open(os.path.join(path, filename)) as file:
        file = file.readlines()

    for i in range(1, len(file) - 1):
        if comment.search(file[i - 1]) and column_names.search(file[i]) and \
                not comment.search(file[i + 1]):
            # this is the column header
            columns = column_names.search(file[i]).groups()[::-1]
            break

    return dataset(columns, data, filename[filename.index('_') + 1:])


def read_experimental_data(graph_name, reacting=False, **kwargs):
    """
    Returns the experimental dataset for a given graph / reacting combination

    Parameters
    ----------
    case: str
        RAS, LES, potential, etc., -- the case to plot
    graph_name: str
        The graph to plot, e.g., meanAxialVelocity
    reacting: bool [False]
        Whether to plot the reacting case or not

    Returns
    -------
    expdata: :class:`dataset`
        The experimental dataset
    """

    if graph_name == 'meanAxialVelocity':
        file = 'Exp_UvsX.txt'
    elif 'axialDeficitPlot' in graph_name:
        file = 'Exp_{}vsY_x={}.txt'
    elif 'fluctuationVelocity' in graph_name:
        file = 'Exp_{}prmsvsY_x={}.txt'

    # translate our coordinate system into experimental
    point = kwargs.pop('point', '')
    vc = kwargs.pop('velocity_component', '')
    vc = 'U' if vc == 'x' else 'V'
    file = file.format(vc, point)

    return read_file(file, reacting)
