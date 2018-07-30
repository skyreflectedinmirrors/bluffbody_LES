#!/usr/bin/env python

"""
 A simple python script to build the mesh / blockMeshDict for the
 Volvo Flygmotor AB LES case

 Automates a few tedious tasks:

 1)  Allows user to specify cell size
 2)  Builds multi-gradings, to avoid having to do crazy calculations inside the
     blockMeshDict

Python 2/3 compatible

Nicholas Curtis - 04/11/18

"""

from __future__ import division, print_function

from collections import defaultdict
from argparse import ArgumentParser
import os

from xml.dom import minidom


def parse_file(file, per_rank):
    def printif(strv):
        if per_rank:
            print(strv)

    xmldoc = minidom.parse(file)
    wtime_dict = defaultdict(lambda: {})
    # get task for total runtime
    tasks = xmldoc.getElementsByTagName('task')
    for task in tasks:
        rank = task.attributes['mpi_rank'].value
        wtime_total = task.getElementsByTagName('perf')[0].attributes[
            'wtime'].value
        wtime_dict[rank]['total'] = float(wtime_total)
        # get each region
        regions = task.getElementsByTagName('region')
        for region in regions:
            name = region.attributes['label'].value
            wtime_dict[rank][name] = float(region.attributes['wtime'].value)
    # check all ranks have same regions
    regions = set()
    for rank in wtime_dict:
        if not regions:
            regions = set(wtime_dict[rank].keys())
        else:
            assert len(set(wtime_dict[rank].keys()) & regions) == len(regions)
    # normalized per rank
    printif('per-rank:')
    for rank in wtime_dict:
        printif('rank = ' + rank)
        wtime = wtime_dict[rank]['total']
        for region in regions:
            printif(region + ' = {}%'.format(
                100. * wtime_dict[rank][region] / wtime))
    printif('')
    printif('')
    print('overall:')
    wtime = sum(wtime_dict[rank]['total'] for rank in wtime_dict)
    for region in regions:
        total = 0
        for rank in wtime_dict:
            total += wtime_dict[rank][region]
        print(region + ' = {}%'.format(100. * total / wtime))


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
    parser.add_argument('-p', '--per_rank',
                        required=False,
                        default=False,
                        action='store_true',
                        help='If true, output the IPM statistic per-rank.')
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
            parse_file(file, args.per_rank)
    else:
        print(args.file)
        parse_file(args.file, args.per_rank)
