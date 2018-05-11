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

from os.path import join
from argparse import ArgumentParser
from string import Template
import re
from textwrap import dedent
import itertools as it

import numpy as np

# problem dimensions
D = 40  # mm
height = 3 * D  # mm
width = 2 * D  # mm
# up/down-stream of bluff-body (from trailing edge)
L_TE_upstream = 200.0  # mm
L_TE_downstream = 682.0  # mm
L_total = 882.0  # mm
BB_height = D * np.sqrt(3.) / 2.  # mm
L_LE_upstream = L_TE_upstream - BB_height  # mm


class grading(object):
    def __init__(self, distance, n_cells, ratio, contraction=False):
        """
        Represents a single grading in an OpenFoam multiGrading block.
        Acts as a convenience object for printing
        """
        self.distance = distance
        self.n_cells = n_cells
        self.ratio = ratio
        if contraction:
            self.ratio = 1. / ratio

    def __repr__(self):
        """ Returns the subgrading string """
        return '({})'.format(' '.join(str(x) for x in (
            self.distance, self.n_cells, self.ratio)))

    def copy(self):
        return self.copy_with()

    def copy_with(self, **kwargs):
        dict = self.__dict__.copy()
        dict.update(**kwargs)
        return grading(**dict)


class blockGrader(object):
    def __init__(self, number, axis, dim, start_size, mesh_size, geometric_ratio,
                 grade_start=True, grade_end=True):
        """
        Parameters
        ----------
        number: int
            The block index
        axis: ['x', 'y', 'z']
            The block-dimension to apply a grading to
        dim: float
            The block's size in the given axis
        start_size: float
            The minimum mesh size
        mesh_size: float
            The mesh size to expand to
        geometric_ratio: float
            The ratio of cell-size growth in this dimension.  Cannot be specified
            at the same time as :param:`expansion_distance`
        grade_start: bool [True]
            If true, grade at the start of this axis
        grade_end: bool [True]
            If true, grade at the end of this axis
        """
        self.num = number
        self.axis = axis
        self.dim = dim
        self.start_size = start_size
        self.mesh_size = mesh_size
        # OpenFOAM treats the expansion ratio as the ratio of the largest cell /
        # to smallest cell,
        self.expansion_ratio = self.mesh_size / self.start_size

        # the geometric ratio is the cell-growth between any two neighbors
        self.geometric_ratio = geometric_ratio
        self.expansion_distance = None
        self.gradings = []
        self.grade_start = grade_start
        self.grade_end = grade_end
        self.children = []
        self.owner = None

    def add_child(self, other):
        assert other.owner is None
        self.children.append(other)
        other.owner = self

    def add_children(self, others):
        for other in others:
            self.add_child(other)

    @property
    def name(self):
        return 'block_{num}_{axis}_grading'.format(num=self.num, axis=self.axis)

    @property
    def cell_name(self):
        axis = self.axis
        if self.owner:
            axis = ''.join(el[0] for el in it.takewhile(
                lambda t: t[0] == t[1], zip(self.axis, self.owner.axis)))
            if axis.endswith('_'):
                axis = axis[:-1]
            if not axis:
                axis = self.axis

        return 'block_{num}_{axis}_cells'.format(num=self.num, axis=axis)

    @property
    def n_cells(self):
        """
        The total number of cells from all sub-gradings of this :class:`blockGrader`
        """

        if not len(self.gradings):
            self.__call__()
        return sum(grad.n_cells for grad in self.gradings)

    def __repr__(self):
        """
        Returns the multigrading block
        """

        if not len(self.gradings):
            self.__call__()
        return '\n'.join(str(grad) for grad in self.gradings)

    def get_subst_dict(self):
        """
        Returns a substitution dictionary for template subs
        """

        n_cells = self.n_cells
        if self.owner:
            n_cells = self.owner.n_cells

        return {self.name: self,
                self.cell_name: n_cells}

    def __check_interior(self, interior):
        if interior < self.mesh_size:
            raise Exception(
                'blockGrading {} along axis {} '
                'with dimension ({}mm) cannot be implemented -- grading '
                'starting with size ({}mm) and geometric ratio {} leaves only '
                '({}mm) the interior mesh, which is smaller than specified mesh '
                'size ({}mm)! Try increasing geometric_ratio'
                ''.format(self.num, self.axis, self.dim, self.start_size,
                          self.geometric_ratio, interior, self.mesh_size))

    def __call__(self, repopulate=False):
        if len(self.gradings) and not repopulate:
            # already populated
            return
        elif repopulate:
            self.gradings = []

        # figure out how many cells are required for this progression
        n_steps = self.solve_geo_progression()
        # and the distance taken
        geo_dist = self.solve_geo_series(n_steps)

        expansion = grading(geo_dist, n_steps, self.expansion_ratio)

        # count gradings
        num_gradings = 0
        if self.grade_start:
            num_gradings += 1
        if self.grade_end:
            num_gradings += 1

        # create dummy interior grading
        interior = self.dim - num_gradings * geo_dist
        self.__check_interior(interior)
        interior_n_cells = int(np.ceil(interior / self.last_geo_size(n_steps)))
        interior = grading(interior, interior_n_cells, 1.0)

        # now add gradings

        # start
        if self.grade_start:
            self.gradings.append(expansion.copy())
        # interior #1
        self.gradings.append(interior.copy())
        # and final contraction
        if self.grade_end:
            self.gradings.append(expansion.copy_with(contraction=True))

        # consistency check
        assert np.isclose(np.sum(grad.distance for grad in self.gradings),
                          self.dim)

    def solve_geo_progression(self):
        """
        Returns the number of cells required to get from a starting mesh size of
        :param:`start_size` to the final size of :param:`mesh_size:`, using the given
        :param:`expansion_ratio`
        """

        # can't solve this
        assert self.geometric_ratio != 1
        assert self.expansion_ratio != 1
        assert self.start_size > 0
        assert self.mesh_size > 0

        if self.geometric_ratio:
            # user specified geometric ratio
            #   -> mesh_size / start_size = geo_ratio^(n_steps - 1)
            n_steps = self.num_expansion_steps()
            # but this isn't exact, so we adjust the expansion ratio such that
            # we keep ~ the same # of steps
            n_steps = int(np.ceil(n_steps))
            # get new ratio
            geometric_ratio = self.get_geometric_ratio(n_steps)
            # sanity check
            assert np.isclose(self.num_expansion_steps(geometric_ratio), n_steps)
            # notify user
            print('Adjusting geometric_ratio from specified {:.5e} to {:.5e} to '
                  'reach mesh size in {} steps'.format(
                    self.geometric_ratio, geometric_ratio, n_steps))
            self.geometric_ratio = geometric_ratio

        else:
            raise NotImplementedError

        return int(n_steps)

    def solve_geo_series(self, n_steps):
        """
        Returns the total distance taken by the geometric series:

            \sum{start_{size} * expansion_{ratio}^{i}}_{i=0}^{n_{steps}}
        """

        assert self.geometric_ratio != 1

        return self.start_size * (1. - np.power(self.geometric_ratio, n_steps)) / (
            1. - self.geometric_ratio)

    def last_geo_size(self, n_steps):
        """
        Returns the size of the last cell at the end of the geometric progression
        """

        assert np.isclose(self.start_size * np.power(self.geometric_ratio, n_steps),
                          self.mesh_size)
        return self.mesh_size

    def num_expansion_steps(self, geometric_ratio=None):
        """
        Returns the number of steps required for a given geometric ratio to reach
        the mesh size from the start_size
        """

        if geometric_ratio is None:
            geometric_ratio = self.geometric_ratio
        return np.log(self.mesh_size / self.start_size) / np.log(geometric_ratio)

    def get_geometric_ratio(self, n_steps):
        """
        Returns the geometric ratio required to reach the mesh size from the start
        size for the given number of steps
        """

        return np.power((self.mesh_size / self.start_size), 1. / (n_steps))


def get_src(case, filename):
    with open(join(case, 'system', '{}.in'.format(filename)), 'r') as file:
        src = file.read()
    return src


def get_template(case, filename):
    return Template(get_src(case, filename))


def _find_indent(template_str, key, value):
    whitespace = None
    for i, line in enumerate(template_str.split('\n')):
        if key in line:
            # get whitespace
            whitespace = re.match(r'\s*', line).group()
            break
    result = [line if i == 0 else whitespace + line for i, line in
              enumerate(dedent(value).splitlines())]
    return '\n'.join(result)


def subs_at_indent(template_str, **kwargs):
    return Template(template_str).safe_substitute(
        **{key: _find_indent(template_str, '${{{key}}}'.format(key=key),
                             value if isinstance(value, str) else str(value))
            for key, value in kwargs.items()})


def main(case, mesh_size, wall_normal, geometric_ratio, long_geometric_ratio):
    # populate mesh dims
    with open(join(case, 'system', 'meshDims'), 'w') as file:
        file.write(get_template(case, 'meshDims').safe_substitute(
            mesh_size=mesh_size))

    # get blockMesh
    src = get_src(case, 'blockMeshDict')

    # and write to file
    with open(join(case, 'system', 'blockMeshDict'), 'w') as file:
        mydict = {}
        graders = []
        # block 0
        block0y = blockGrader(0, 'y', height / 2., wall_normal, mesh_size,
                              geometric_ratio)
        graders.append(block0y)
        graders.append(blockGrader(0, 'z', L_LE_upstream, wall_normal, mesh_size,
                                   geometric_ratio, grade_end=False))
        # block 1
        block1y = blockGrader(1, 'y', height / 2., wall_normal, mesh_size,
                              geometric_ratio)
        graders.append(block1y)
        graders.append(blockGrader(1, 'z', L_LE_upstream, wall_normal, mesh_size,
                                   geometric_ratio, grade_end=False))
        # block 2
        block2y_short = blockGrader(2, 'y_short', D, wall_normal, mesh_size,
                                    geometric_ratio)
        block2y_long = blockGrader(2, 'y_long', D * 1.5, wall_normal, mesh_size,
                                   geometric_ratio)
        graders.append(block2y_short)
        graders.append(block2y_long)
        graders.append(blockGrader(2, 'z', BB_height, wall_normal, mesh_size,
                                   geometric_ratio))

        # block 3
        block3y_short = blockGrader(3, 'y_short', D, wall_normal, mesh_size,
                                    geometric_ratio)
        block3y_long = blockGrader(3, 'y_long', D * 1.5, wall_normal, mesh_size,
                                   geometric_ratio)
        graders.append(block3y_short)
        graders.append(block3y_long)
        graders.append(blockGrader(3, 'z', BB_height, wall_normal, mesh_size,
                                   geometric_ratio))

        # block 4
        block4y = blockGrader(4, 'y', D, wall_normal, mesh_size,
                              geometric_ratio)
        graders.append(block4y)
        graders.append(blockGrader(4, 'z', L_TE_downstream, wall_normal, mesh_size,
                                   long_geometric_ratio, grade_start=False))

        # block 5
        graders.append(blockGrader(5, 'y', D, wall_normal, mesh_size,
                                   geometric_ratio))
        graders.append(blockGrader(5, 'z', L_TE_downstream, wall_normal, mesh_size,
                                   long_geometric_ratio, grade_start=False))

        # block 6
        block6y = blockGrader(6, 'y', D, wall_normal, mesh_size,
                              geometric_ratio)
        graders.append(block6y)
        graders.append(blockGrader(6, 'z', L_TE_downstream, wall_normal, mesh_size,
                                   long_geometric_ratio, grade_start=False))

        # setup children
        block2y_short.add_children([block2y_long, block0y, block4y])
        block3y_short.add_children([block3y_long, block1y, block6y])

        for grader in graders:
            mydict.update(grader.get_subst_dict())
        file.write(subs_at_indent(src, **mydict))


if __name__ == '__main__':
    parser = ArgumentParser('buildMesh.py -- set up blockMeshDict for Volvo '
                            'Flygmotor LES simulation.')
    parser.add_argument('-c', '--case',
                        required=True,
                        type=str,
                        help='The path to the OpenFOAM case to build the block mesh'
                             ' for.')
    parser.add_argument('-m', '--mesh_size',
                        type=float,
                        default=2.,
                        help='The background mesh resolution in millimeters '
                             '(e.g., 2 mm)')
    parser.add_argument('-w', '--wall_normal',
                        type=float,
                        default=0.3,
                        help='The minimum wall normal distance in millimeters '
                             '(e.g., 0.3 mm)')
    parser.add_argument('-g', '--geometric_ratio',
                        type=float,
                        default=1.15,
                        help='The geometric-ratio of cells size increases.'
                             'Incompatible with expansion_distance option.')
    parser.add_argument('-l', '--long_geometric_ratio',
                        type=float,
                        default=1.05,
                        help='The geometric-ratio of (slow) cell size increases.'
                             'Incompatible with expansion_distance option.')
    args = parser.parse_args()
    main(args.case, args.mesh_size, args.wall_normal, args.geometric_ratio,
         args.long_geometric_ratio)
