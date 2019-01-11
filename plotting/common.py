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
import matplotlib.pyplot as plt
plt.rc('text', usetex=True)
plt.rc('text.latex', preamble=r'\usepackage{amsmath}')

script_dir = os.path.abspath(os.path.dirname(__file__))


class dimensions(object):
    def __init__(self, reacting=False):
        self.D = 40 / 1000  # mm
        self.height = 3 * self.D
        self.width = 2 * self.D
        self.Ubulk = 16.6 if not reacting else 17.6  # m/s
        self.trailing_edge = -200 / 1000  # mm
        self.z_offset = self.trailing_edge  # mm
        self.y_offset = self.height / 2  # mm
        self.z_flip = -1


class dataset(object):
    def __init__(self, columns, data, name, is_simulation=False, time=None):
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
        self.time = time

        assert len(columns) == data.shape[-1]

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

    def normalize(self, reacting=False, velocity_power=1.0):
        assert self.is_simulation, "I don't know how to normalize experimental data"

        dims = dimensions(reacting)
        for i, col in enumerate(self.columns):
            if col in ['y', 'z']:
                # correct dimensions
                offset = getattr(dims, '{}_offset'.format(col), 0)
                self.data[:, i] -= offset
                # flip axes?
                flip = getattr(dims, '{}_flip'.format(col), 1)
                self.data[:, i] *= flip
                # normalize
                self.data[:, i] /= dims.D
            elif col in ['Ux', 'Uy', 'Uz']:
                axis = col[-1]
                if 'fluct' not in self.name:
                    # flip axes?
                    flip = getattr(dims, '{}_flip'.format(axis), 1)
                    self.data[:, i] *= flip
                Ubulk = np.power(dims.Ubulk, velocity_power)
                # and normalize
                self.data[:, i] /= Ubulk

    def __mul__(self, other):
        assert isinstance(other, dataset)
        assert self.is_simulation == other.is_simulation
        assert np.array_equal(self.time, other.time)
        data = self.data.copy()
        slicer = [slice(None) for x in data.shape]
        slicer[-1] = slice(1, data.shape[-1])
        data[slicer] *= other.data[slicer]
        return dataset(self.columns, data,
                       '{} x {}'.format(self.name, other.name),
                       self.is_simulation, time=self.time)


class PlotStyles(object):
    def __init__(self, cases, grey=False):
        self.num_colors = len(cases) + 1  # for experimental data
        self.grey = grey

    @property
    def color_map(self):
        cmap = 'Greys' if self.grey else 'inferno'
        return plt.get_cmap(cmap, self.num_colors + 1)


class UserOptions(object):
    """
    A simple class that holds the various user-specified options
    """

    def __init__(self, cases, reacting, t_start=0, t_end=-1,
                 base_path=None, out_path=None, velocity_component='both'):
        self.cases = cases
        self.reacting = reacting
        self.t_start = t_start
        self.t_end = t_end
        self.base_path = base_path
        self.out_path = out_path
        self.velocity_component = velocity_component
        if self.velocity_component == 'both':
            self.velocity_component = ['z', 'y']
        else:
            self.velocity_component = [self.velocity_component]
        # fix case paths
        self.cases = self.get_cases()
        if self.out_path is None:
            self.out_path = script_dir

        # plot styles
        self.style = PlotStyles(self.cases)

    @property
    def ncases(self):
        return len(self.cases)

    def get_simulation_path(self, case, graph_name):
        """
        Return the path to a simulation graph directory
        """
        path = pjoin(self.base_path, case, 'postProcessing', graph_name)
        path = os.path.abspath(path)

        if not pisdir(path):
            raise Exception('Graph {} for case {} {} not found, {} is not a valid '
                            'directory'.format(
                                graph_name,
                                'reacting' if self.reacting else 'non-reacting',
                                case, path))

        return path

    def make_dir(self, case):
        import os
        if not os.path.exists(pjoin(self.out_path, case)):
            os.makedirs(pjoin(self.out_path, case))

    def get_cases(self):
        # get path
        if self.base_path:
            self.base_path = os.path.abspath(self.base_path)
        else:
            self.base_path = os.path.abspath(pjoin(script_dir, ppardir))
        react_str = 'reacting' if self.reacting else 'non-reacting'
        self.base_path = pjoin(self.base_path, react_str)
        return [pjoin(self.base_path, case) for case in self.cases]

    def color(self, caseno, exp=False):
        return self.style.color_map(caseno + 1 if not exp else 0)


class Plot(object):
    def __init__(self, sim_name, opts,
                 read_exp_kwargs={},
                 label_names={},
                 exp_name=None,
                 sharey=False,
                 sharex=False):
        base_label_names = {'mean': 'Simulation',
                            'U': r'$u/U_{\text{bulk}}$',
                            'V': r'$v/U_{\text{bulk}}$',
                            'U\'rms': r"$u'_{\text{rms}}/U_{\text{bulk}}$",
                            'V\'rms': r"$v_{\text{rms}}/U_{\text{bulk}}$",
                            'Y': r'$y/D$',
                            'X': r'$x/D$',
                            'AVG(U\'V\')/(Ubulk)^2 (Reynolds Stress Approx)':
                                r'Mean $\frac{u^\prime v^\prime}{U_{\text{bulk}}^2}$'
                            }
        base_label_names.update(label_names)
        self._sim_name = sim_name
        if exp_name is None:
            exp_name = sim_name
        self._exp_name = exp_name
        self.opts = opts

        self.read_exp_kwargs = read_exp_kwargs.copy()
        self.label_names = base_label_names.copy()
        self.sharex = sharex
        self.sharey = sharey
        self.axes = []
        self.fig = plt.figure(figsize=self.figsize())

    @property
    def multiplot(self):
        return self.sharex or self.sharey

    @property
    def gca(self):
        return self.axes[-1] if self.multiplot else plt.gca()

    @property
    def num_plots(self):
        if self.multiplot:
            return self.sharex if self.sharex else self.sharey
        return 1

    @property
    def shared(self):
        return self.axes[0] if self.axes else None

    def process(self, caseno, case, **kwargs):
        from read_simulation_data import read_simulation_data
        # read baseline averaged data
        simdata = read_simulation_data(case, self.sim_name(**kwargs),
                                       self.opts, **kwargs)
        # normalize / convert simulation data
        simdata.normalize(simdata)
        pltargs = {}
        if (self.multiplot and not kwargs.get('hold', False)) or not self.multiplot:
            pltargs['label'] = self.label(simdata.name, case)
        col_map = self.simulation_column_map()
        self.gca.plot(simdata[:, col_map[0]], simdata[:, col_map[1]],
                      color=self.opts.color(caseno), **pltargs)

    def sim_name(self, **kwargs):
        return self._sim_name

    def exp_name(self, **kwargs):
        return self._exp_name

    def plot(self, hold=None, **kwargs):
        for caseno, casename in enumerate(self.opts.cases):
            if self.multiplot:
                if self.sharex:
                    ax = self.fig.add_subplot(
                        self.num_plots, 1, hold + 1, sharex=self.shared)
                else:
                    ax = self.fig.add_subplot(
                        1, self.num_plots, hold + 1, sharey=self.shared)
                self.axes.append(ax)
            self.opts.make_dir(casename)
            self.process(caseno, casename, hold=hold, **kwargs)
            self.plot_experimental(hold=hold, **kwargs)
            if self.multiplot:
                self.gca.set_title(self.title(**kwargs))
                self.gca.set_xlim(self.xlim())
                self.gca.set_ylim(self.ylim())

        if hold is None:
            self.finalize(**kwargs)

    def finalize(self, **kwargs):
        legend_font = 30
        major_font = 30
        minor_font = 24
        label_size = 30
        if not self.multiplot:
            self.gca.legend(loc=0, fontsize=legend_font)
            self.gca.set_xlim(self.xlim())
            self.gca.set_ylim(self.ylim())
            self.gca.set_title(self.title(**kwargs))
            self.gca.tick_params(axis='both', which='major',
                                 labelsize=major_font)
            self.gca.tick_params(axis='both', which='minor',
                                 labelsize=minor_font)
            for item in (self.gca.title, self.gca.xaxis.label,
                         self.gca.yaxis.label):
                item.set_fontsize(label_size)
        else:
            for ax in self.axes:
                ax.tick_params(axis='both', which='major',
                               labelsize=major_font)
                ax.tick_params(axis='both', which='minor',
                               labelsize=minor_font)
                for item in (ax.title, ax.xaxis.label, ax.yaxis.label):
                    item.set_fontsize(label_size)
            self.fig.legend(bbox_to_anchor=(0.06, 1.02, 1, 0.2), loc="lower left",
                            borderaxespad=0, ncol=3, fontsize=legend_font,
                            labelspacing=8)
        self.fig.tight_layout()
        self.fig.savefig(pjoin(self.opts.out_path, self.figname()),
                         bbox_inches="tight")
        plt.close(self.fig)

    def figname(self):
        raise NotImplementedError

    def label(self, name, case):
        label = name
        if label in self.label_names:
            label = self.label_names[label]
        if self.opts.ncases > 1:
            label += ' ({})'.format(case)
        return label

    def nice_labelname(self, label):
        if label in self.label_names:
            return self.label_names[label]
        return label

    def title(self, **kwargs):
        return ""

    def xlim(self):
        return (None, None)

    def ylim(self):
        return (None, None)

    def figsize(self):
        return (6.4, 4.8)

    def plot_experimental(self, **kwargs):
        from read_experimental_data import read_experimental_data
        expdata = read_experimental_data(self.exp_name(**kwargs),
                                         self.opts.reacting,
                                         **kwargs)

        col_map = self.exp_column_map()
        pltargs = {}
        if (self.multiplot and not kwargs.get('hold', False)) or not self.multiplot:
            pltargs['label'] = 'Experimental'
        self.gca.scatter(expdata[:, col_map[0]], expdata[:, col_map[1]],
                         color=self.opts.color(0, exp=True),
                         **pltargs)

        self.gca.set_xlabel(self.nice_labelname(expdata.columns[col_map[0]]))
        self.gca.set_ylabel(self.nice_labelname(expdata.columns[col_map[1]]))

    def simulation_column_map(self):
        return (0, 1)

    def exp_column_map(self):
        return (1, 0)


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
    parser.add_argument('-c', '--caselist',
                        type=str,
                        help='The simulation(s) to plot. If more than one simulation'
                             ' is supplied, they will be plotted on the same figure'
                             " in the first supplied case's directory.",
                        nargs='+',
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
    parser.add_argument('-p', '--base_path',
                        default=None,
                        type=str,
                        help='The base path to the top-level folder that contains '
                             'the non-reacting and reacting cases.')
    parser.add_argument('-o', '--out_path',
                        required=False,
                        default=None,
                        help='The path to place the generated plots in. '
                             'If not supplied, stores in the case-directory')
    return parser
