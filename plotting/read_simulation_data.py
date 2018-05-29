"""
read_simulation_data.py -- a utility to read in experimental data from
OpenFoam postProcessing directories

Nick Curtis

04/19/2018
"""

from __future__ import division

import os as os
from os.path import join as pjoin
from os import listdir as plistdir
from os.path import isfile as pisfile
from os.path import isdir as pisdir
from os.path import basename as pasename

from scipy.integrate import simps, trapz
import numpy as np

from common import dataset, get_simulation_path

script_dir = os.path.abspath(os.path.dirname(__file__))


def get_graph_columns(graph_name, **kwargs):
    """
    Returns the expected filename, and column names for a given graph
    """

    if graph_name == 'meanAxialVelocity':
        return 'line_U.xy', ('z', 'Uz'), (0, 3)
    elif 'axialDeficitPlot' in graph_name:
        # translate experimental component
        vc = kwargs.pop('velocity_component')
        vc = 'U{}'.format(vc)
        index = ['axis', 'Ux', 'Uy', 'Uz'].index(vc)
        return 'line_U.xy', ('y', vc), (0, index)


class integration_averager(object):
    """
    Computes the time-average of a quantity via numerical integration
    """

    def __init__(self, method='simps'):
        if method == 'simps':
            self.method = simps
        elif method == 'trapz':
            self.method = trapz
        else:
            raise NotImplementedError()

    def __call__(self, data, time, axis=0):
        # integrate
        integrated = self.method(data, time, axis=axis)
        # and average
        return integrated / (time[-1] - time[0])


class RMS(object):
    """
    Compute the RMS of a quantity, possibly with respect to baseline data (i.e.,
    a fluctuation velocity)
    """

    def __init__(self, baseline=None):
        self.baseline = baseline

    def __call__(self, data, time, axis=0):

        # the axis supplied corresponds to different time-increments, however unlike
        # in averaging we want to take the difference over all times

        assert axis == 0

        # fluctuation across space
        fluct = data - self.baseline[:, 1]
        # square all samples
        fluct = fluct * fluct
        # average over time
        fluct = integration_averager()(fluct, time)
        # root
        return np.sqrt(fluct)


def read_simulation_data(case, graph_name, reacting=False, t_start=0, t_end=-1,
                         collection_type='mean', collection_method='simps',
                         baseline=None, **kwargs):
    """
    Read and process data for a given case, graph and reacting/non-reacting
    simulation.

    Parameters
    ----------
    case: str
        The case name, e.g., LES, RAS, potential
    graph_name: str
        The graph to produce, corresponding to the OpenFOAM function objects, e.g.,
        meanAxialVelocity or axialDeficitPlot_0p95
    reacting: bool [False]
        Whether to produce the reacting or non-reacting
    t_start: float
        The start time, in seconds of the simulation window to read
    t_end: float
        The end time, in seconds of the simulation window to read.
        If < 0, end time is disabled.
    collection_type: {'mean', 'fluct'}
        The type of data to collect:
            - mean: compute the time-averaged value of the simulation velocities
                    Note: :param:`collection_method` must be 'simps' or 'trapz'
            - fluct: compute the fluctuation velocity relative to the time-averaged
                     value.  Note: :param:`collection_method` must be 'rms', and
                     :param:`baseline` should be supplied
    collection_method: {'simps', 'trapz', 'rms'}
        The method to use while processing the simulation data:
            - 'simps': use the scipy simps function to integrate the data,
            corresponds to :param:`collection_type` == 'mean'
            - 'trapz': use the scipy trapz function to integrate the data,
            corresponds to :param:`collection_type` == 'mean'
            - 'rms': compute the root-mean-square value of the simulation data

    Returns
    -------
    data: :class:`dataset`
        The time-averaged (or not) simulation data
    """

    assert t_start >= 0, 'Start time < 0 not supported'
    assert t_end < 0 or t_end > t_start, (
        'End time must be disabled or greater than start time')

    # collection type
    collector = None
    if collection_method in ['simps', 'trapz']:
        collector = integration_averager(collection_method)
        assert collection_type == 'mean'
    elif collection_method == 'rms':
        assert collection_type == 'fluct'
        assert baseline is not None
        collector = RMS(baseline)
    else:
        raise Exception('Unknown collection method: {}'.format(collection_method))

    path = get_simulation_path(case, graph_name, reacting)
    efile, columns, use_columns = get_graph_columns(graph_name, **kwargs)

    datalist = []
    timelist = []
    for time_dir in sorted([pjoin(path, x) for x in plistdir(path)
                           if pisdir(pjoin(path, x))]):
        # check that it's a valid time directory
        try:
            time = float(pasename(time_dir))
            if time < t_start or (t_end > 0 and time > t_end):
                # out of range
                continue
        except ValueError:
            print('Skipping directory {} for graph {}, not a time-directory'.format(
                pasename(time_dir), graph_name))
            continue
        # get file list
        files = [pjoin(time_dir, x) for x in plistdir(time_dir)
                 if pisfile(pjoin(time_dir, x))]
        if len(files) > 1:
            raise NotImplementedError
        # open file
        file = files[0]
        base = pasename(file)
        if base != efile:
            raise Exception('File type {} for graph type {} unexpected'.format(
                base, graph_name))

        # read file
        data = np.loadtxt(file, usecols=use_columns)
        if not data.size:
            print('Data for time directory {} empty, skipping.'.format(
                time))
            continue
        datalist.append(data)
        timelist.append(time)

    # sanity check -- ensure all data is same shape
    assert np.all([x.shape == datalist[0].shape for x in datalist])

    # check time is ordered
    assert np.all([timelist[i + 1] > timelist[i] for i in range(len(timelist) - 1)])

    # ensure we have same times and data
    assert len(timelist) == len(datalist)

    # finally, average the data over time
    time = np.array(timelist)
    complete_data = np.array(datalist)

    final_data = np.zeros(complete_data.shape[1:])
    # simply copy in coordinate axes
    assert np.all(np.array_equal(x[:, 0], complete_data[0, :, 0])
                  for x in complete_data)
    final_data[:, 0] = complete_data[0, :, 0]

    for var in range(1, complete_data.shape[2]):
        # get collected data
        final_data[:, var] = collector(complete_data[:, :, var], time, axis=0)

    return dataset(columns, final_data, collection_type, is_simulation=True)
