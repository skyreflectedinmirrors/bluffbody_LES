"""
common.py -- a set of common data objects / plotting styles for plotting of
Volvo LES bluff-body

Nick Curtis

04/19/2018
"""
import os
from os.path import join as pjoin
from os.path import pardir as ppardir
from os.path import isdir as pisdir
import numpy as np

script_dir = os.path.abspath(os.path.dirname(__file__))


class dataset(object):
    def __init__(self, columns, data, name):
        """
        Attributes
        ----------
        columns: list of str
            The column header names, read from the experimental data
        data: numpy array of shape (len(columns), :attr:`npoints`)
            The data in the experimental data set
        name: str
            The experimental data filename, describing the data within
        """

        self.columns = columns[:]
        self.data = np.copy(data)
        self.name = name

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
