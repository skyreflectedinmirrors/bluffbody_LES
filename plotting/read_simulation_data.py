"""
read_simulation_data.py -- a utility to read in experimental data from
OpenFoam postProcessing directories

Nick Curtis

04/19/2018
"""

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


def get_graph_columns(graph_name):
    """
    Returns the expected filename, and column names for a given graph
    """

    if graph_name == 'meanAxialVelocity':
        return 'line_U.xy', ('z', 'Uz'), (0, 3)
    else:
        raise NotImplementedError


def read_simulation_data(case, graph_name, reacting=False, t_start=0, t_end=-1,
                         averaging_type='simps'):
    """
    Read and process data for a given case, graph and reacting/non-reacting
    simulation.

    Parameters
    ----------
    case: str
        The case name, e.g., LES, RAS, potential
    graph_name: str
        The graph to produce, corresponding to the OpenFOAM function objects, e.g.,
        meanAxialVelocity or axialDeficitPlot_0point95
    reacting: bool [False]
        Whether to produce the reacting or non-reacting
    t_start: float
        The start time, in seconds of the simulation window to read
    t_end: float
        The end time, in seconds of the simulation window to read.
        If < 0, end time is disabled.
    averaging_type: str ['simps', 'trapz']
        Average the simulation data using this scipy method

    Returns
    -------
    data: :class:`dataset`
        The time-averaged (or not) simulation data
    """

    assert t_start >= 0, 'Start time < 0 not supported'
    assert t_end < 0 or t_end > t_end, (
        'End time must be disabled or greater than start time')

    # integrator type
    integrator = None
    if averaging_type == 'simps':
        integrator = simps
    elif averaging_type == 'trapz':
        integrator = trapz
    else:
        raise Exception('Unknown averaging type: {}'.format(averaging_type))

    path = get_simulation_path(case, graph_name, reacting)
    efile, columns, use_columns = get_graph_columns(graph_name)

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
    assert np.all(x.shape == datalist[0].shape for x in datalist)

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
        # integrate
        final_data[:, var] = integrator(complete_data[:, :, var], time, axis=0)
        # and average
        final_data[:, var] /= (time[-1] - time[0])

    return dataset(columns, final_data, 'Simulation')
