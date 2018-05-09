"""
common.py -- a set of common data objects / plotting styles for plotting of
Volvo LES bluff-body

Nick Curtis

04/19/2018
"""
from __future__ import division

from argparse import ArgumentParser
import os
from os.path import join as pjoin
from os.path import pardir as ppardir
from os.path import isdir as pisdir
import numpy as np

script_dir = os.path.abspath(os.path.dirname(__file__))


class dimensions(object):
    def __init__(self, reacting=False):
        self.D = 40 / 1000  # mm
        self.height = 3 * self.D
        self.width = 2 * self.D
        self.Ubulk = 16.6 if not reacting else 17.6  # m/s
        self.z_offset = 0  # mm
        self.y_offset = 0  # mm


class dataset(object):
    def __init__(self, columns, data, name, is_simulation=False):
        """
        Attributes
        ----------
        columns: list of str
            The column header names, read from the experimental data
        data: numpy array of shape (len(columns), :attr:`npoints`)
            The data in the experimental data set
        name: str
            The experimental data filename, describing the data within
        is_simulation: bool [False]
            Whether the data is from a simulation or not
        """

        self.columns = columns[:]
        self.data = np.copy(data)
        self.name = name
        self.is_simulation = is_simulation

        assert len(columns) == data.shape[1]

    @property
    def npoints(self):
        """
        The number of data points in this data set
        """
        return self.data.shape[1]

    @property
    def shape(self):
        return self.data.shape

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    def normalize(self, reacting=False):
        assert self.is_simulation, "I don't know how to normalize experimental data"

        dims = dimensions(reacting)
        for i, col in enumerate(self.columns):
            if col in ['x', 'y']:
                # correct dimensions
                offset = getattr(dims, '{}_offset'.format(col), 0)
                self.data[:, i] -= offset
                # normalize
                self.data[:, i] /= dims.D
            elif col in ['Ux', 'Uy', 'Uz']:
                Ubulk = dims.Ubulk
                # and normalize
                self.data[:, i] /= Ubulk


def get_simulation_path(case, graph_name, reacting=False):
    """
    Return the path to a simulation graph directory
    """
    # get path
    react_str = 'reacting' if reacting else 'non-reacting'
    path = pjoin(script_dir, ppardir, react_str, case, 'postProcessing', graph_name)
    path = os.path.abspath(path)

    if not pisdir(path):
        raise Exception('Graph {} for case {} {} not found, {} is not a valid '
                        'directory'.format(graph_name, react_str, case, path))

    return path


def make_dir(case):
    import os
    if not os.path.exists(pjoin(script_dir, case)):
        os.makedirs(pjoin(script_dir, case))


def get_default_parsing_args(name, description):
    parser = ArgumentParser('{name}: {description}'.format(
        name=name, description=description))
    parser.add_argument('-r', '--reacting',
                        help='Plot the reacting-flow data.',
                        action='store_true',
                        dest='reacting',
                        default=False,
                        required=False)
    parser.add_argument('-n', '--non_reacting',
                        help='Plot the reacting-flow data.',
                        action='store_false',
                        dest='reacting',
                        required=False)
    parser.add_argument('-c', '--case',
                        help='The simulation to plot',
                        choices=['LES', 'RAS'],
                        required=True)
    parser.add_argument('-t_start', '--start_time',
                        help='The start time for simulation averaging in seconds.',
                        required=False,
                        type=float,
                        default=0)
    parser.add_argument('-t_end', '--end_time',
                        help='The end time for simulation averaging in seconds.',
                        required=False,
                        type=float,
                        default=-1)
    return parser
