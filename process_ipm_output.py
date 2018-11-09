#!/usr/bin/env python

"""
A simple script to parse IPM timing results from OpenFOAM runs

Python 2/3 compatible

Nicholas Curtis (c)

04/11/18
--------
Create initial version of parser

11/9/18
-------
Update parser to include different stats types and be aware of multiple time-steps
in an IPM run (previously it took 4 hours to run a single reacting time-step, so
this wasn't an issue)
"""

from __future__ import division, print_function

from collections import OrderedDict, Callable
from argparse import ArgumentParser, ArgumentError
import os

import numpy as np
from xml.dom import minidom


class DefaultOrderedDict(OrderedDict):
    # Source: http://stackoverflow.com/a/6190500/562769
    def __init__(self, default_factory=None, *a, **kw):
        if (default_factory is not None and
           not isinstance(default_factory, Callable)):
            raise TypeError('first argument must be callable')
        OrderedDict.__init__(self, *a, **kw)
        self.default_factory = default_factory

    def __getitem__(self, key):
        try:
            return OrderedDict.__getitem__(self, key)
        except KeyError:
            return self.__missing__(key)

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = value = self.default_factory()
        return value

    def __reduce__(self):
        if self.default_factory is None:
            args = tuple()
        else:
            args = self.default_factory,
        return type(self), args, None, None, self.items()

    def copy(self):
        return self.__copy__()

    def __copy__(self):
        return type(self)(self.default_factory, self)

    def __deepcopy__(self, memo):
        import copy
        return type(self)(self.default_factory,
                          copy.deepcopy(self.items()))

    def __repr__(self):
        return 'OrderedDefaultDict(%s, %s)' % (self.default_factory,
                                               OrderedDict.__repr__(self))


def new_dict(default=None):
    if default is None:
        return DefaultOrderedDict(new_dict)
    else:
        return DefaultOrderedDict(lambda: default)


class stats(object):
    def __init__(self, name, per_rank, per_step=True, results=None,
                 aggregate=None):
        self.name = name
        self.per_rank = per_rank
        self.per_step = per_step
        if results is None:
            self.results = new_dict()
        else:
            self.results = results
        if aggregate is None:
            self._aggregate = new_dict(0)
            self._aggregate['total'] = new_dict(0)
        else:
            self._aggregate = aggregate

    def __call__(self, rank, region, rank_walltime, total_walltime, n_steps):
        raise NotImplementedError

    def __str__(self):
        return self.__repr__()

    def rank_result(self, rank, region):
        raise NotImplementedError

    def result(self, region):
        raise NotImplementedError

    def aggregate(self, region):
        raise NotImplementedError

    def __repr__(self):
        out = []
        if self.per_rank:
            for rank in sorted(self.results):
                out.append('rank = {}'.format(rank))
                for region in self.results[rank]:
                    out.append(self.rank_result(rank, region))
        else:
            for region in sorted(self._aggregate):
                if region == 'total':
                    continue
                self.aggregate(region)
                out.append(self.result(region))
        return '\n'.join(out)


class max_time(stats):
    def __init__(self, per_rank, per_step=True):
        dmin = -np.finfo(np.float64).max
        super(max_time, self).__init__(
            'max', per_rank, per_step=per_step,
            results=new_dict(new_dict(dmin)),
            aggregate=new_dict(dmin))

    def __call__(self, rank, region, rank_walltime, total_walltime, n_steps):
        self.results[rank][region] = np.maximum(
            rank_walltime, self.results[rank][region])
        self._aggregate[region] = np.maximum(
            rank_walltime, self._aggregate[region])
        self._aggregate['total'] = np.maximum(
            total_walltime, self._aggregate['total'])

    def rank_result(self, rank, region):
        return region + ' = {}(s)'.format(self.results[rank][region])

    def result(self, region):
        return region + ' = {}(s)'.format(self._aggregate[region])

    def aggregate(self, region):
        pass


class min_time(stats):
    def __init__(self, per_rank, per_step=True):
        dmax = np.finfo(np.float64).max
        super(min_time, self).__init__(
            'min', per_rank, per_step=per_step,
            results=new_dict(new_dict(dmax)),
            aggregate=new_dict(dmax))

    def __call__(self, rank, region, rank_walltime, total_walltime, n_steps):
        self.results[rank][region] = np.minimum(
            rank_walltime, self.results[rank][region])
        self._aggregate[region] = np.minimum(
            rank_walltime, self._aggregate[region])
        self._aggregate['total'] = np.minimum(
            total_walltime, self._aggregate['total'])

    def rank_result(self, rank, region):
        return region + ' = {}(s)'.format(self.results[rank][region])

    def result(self, region):
        return region + ' = {}(s)'.format(self._aggregate[region])

    def aggregate(self, region):
        pass


class percent_time(stats):
    def __init__(self, per_rank, per_step=True):
        super(percent_time, self).__init__('percent', per_rank, per_step=per_step)

    def __call__(self, rank, region, rank_walltime, total_walltime, n_steps):
        self.results[rank][region] = 100. * rank_walltime / total_walltime
        self._aggregate[region] += rank_walltime
        if rank not in self._aggregate['total']:
            self._aggregate['total'][rank] = total_walltime
        else:
            assert self._aggregate['total'][rank] == total_walltime

    def rank_result(self, rank, region):
        return region + ' = {}%'.format(self.results[rank][region])

    def result(self, region):
        return region + ' = {}%'.format(self._aggregate[region])

    def aggregate(self, region):
        total = 0
        for rank in self._aggregate['total']:
            total += self._aggregate['total'][rank]
        self._aggregate[region] = 100. * self._aggregate[region] / total


class sum_time(stats):
    def __init__(self, per_rank, per_step=True):
        super(sum_time, self).__init__('sum', per_rank, per_step=per_step,
                                       results=new_dict(new_dict(0)))

    def __call__(self, rank, region, rank_walltime, total_walltime, n_steps):
        self.results[rank][region] += rank_walltime
        self._aggregate[region] += rank_walltime
        if rank not in self._aggregate['total']:
            self._aggregate['total'][rank] += total_walltime
        else:
            assert self._aggregate['total'][rank] == total_walltime

    def rank_result(self, rank, region):
        return region + ' = {}(s)'.format(self.results[rank][region])

    def result(self, region):
        return region + ' = {}(s)'.format(self._aggregate[region])

    def aggregate(self, region):
        total = 0
        for rank in self._aggregate['total']:
            total += self._aggregate['total'][rank]
        return total


def stat_type(stat_type):
    stats_types = [max_time(0), min_time(0), percent_time(0),
                   sum_time(0)]
    stat = next((x for x in stats_types if x.name == stat_type.lower()), None)
    if not stat:
        raise ArgumentError(
            None, "Invalid statistics type '{}'. Valid choices are: ({})".format(
                stat_type, ', '.join([x.name for x in stats_types])))

    return stat.__class__


def parse_file(file, per_rank, per_step, stat_class):
    xmldoc = minidom.parse(file)
    wtime_dict = new_dict()
    # get task for total runtime
    tasks = xmldoc.getElementsByTagName('task')
    for task in sorted(tasks, key=lambda x: int(x.attributes['mpi_rank'].value)):
        rank = task.attributes['mpi_rank'].value
        wtime_total = task.getElementsByTagName('perf')[0].attributes[
            'wtime'].value
        wtime_dict[rank]['total'] = float(wtime_total)
        # get each region
        regions = task.getElementsByTagName('region')
        for region in sorted(regions, key=lambda x: x.attributes['label'].value):
            name = region.attributes['label'].value
            wtime_dict[rank][name]['total'] = float(region.attributes['wtime'].value)
            if name == 'species_convection':
                # get the number of time-steps
                assert 'steps' not in wtime_dict[rank]
                wtime_dict[rank]['steps'] = int(region.attributes['nexits'].value)
    # check all ranks have same regions & same number of time-steps
    regions = set()
    n_steps = None
    for rank in wtime_dict:
        if not regions:
            regions = set(wtime_dict[rank].keys())
            n_steps = wtime_dict[rank]['steps']
        else:
            assert len(set(wtime_dict[rank].keys()) & regions) == len(regions)
            assert wtime_dict[rank]['steps'] == n_steps

    regions -= set(['total', 'steps'])

    # create stat's object
    statistics = stat_class(per_rank, per_step)
    for rank in wtime_dict:
        total_walltime = wtime_dict[rank]['total']
        for region in regions:
            rank_walltime = wtime_dict[rank][region]['total']
            if per_step:
                rank_walltime /= n_steps
                total_walltime /= n_steps
            statistics(rank, region, rank_walltime, total_walltime, n_steps)

    print(statistics)
    print('\n\n')


if __name__ == '__main__':
    parser = ArgumentParser('process_ipm_output.py -- process profiling output')
    parser.add_argument('-f', '--file',
                        required=False,
                        type=str,
                        help='The path to the IPM output xml file.')
    parser.add_argument('-d', '--directory',
                        required=False,
                        type=str,
                        help='A path to IPM XML output files to parse.')
    parser.add_argument('-r', '--per_rank',
                        required=False,
                        default=False,
                        action='store_true',
                        help='If true, output the IPM statistic per-rank.')
    parser.add_argument('-n', '--not_per_step',
                        required=False,
                        dest='per_step',
                        default=True,
                        action='store_false',
                        help='If true, output the IPM statistic per time-step.')
    parser.add_argument('-t', '--stats_type',
                        required=False,
                        default=percent_time,
                        type=stat_type
                        )
    args = parser.parse_args()
    if not (args.directory or args.file):
        raise Exception('Must specify at least one file or directory')
    if args.directory:
        # load files
        files = [os.path.join(args.directory, file) for file in os.listdir(
            args.directory)]
        files = [file for file in files if os.path.isfile(file) and file.endswith(
            '.xml')]
        for file in files:
            print(os.path.basename(file))
            parse_file(file, args.per_rank, args.per_step, args.stats_type)
    else:
        print(args.file)
        parse_file(args.file, args.per_rank, args.per_step, args.stats_type)
