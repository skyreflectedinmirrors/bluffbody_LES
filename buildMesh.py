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
import numpy as np


# problem dimensions
D = 40  # mm
height = 3 * D  # mm
width = 2 * D  # mm
# total channel length
length = 782.0  # mm
# up/down-stream of bluff-body (from trailing edge)
L_TE_upstream = 100.0  # mm
L_TE_downstream = 682.0  # mm
L_total = 782.0  # mm
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
                 expansion_distance, grade_at_midpoint=False, grade_start=True,
                 grade_end=True):
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
        expansion_distance: float
            The percent of :param:`dim` that should be taken up by one grading
        grade_at_midpoint: bool [False]
            If true, add grading in both directions at midpoint
        grade_start: bool [True]
        """
        self.num = number
        assert axis in ['x', 'y', 'z']
        self.axis = axis
        self.dim = dim
        self.start_size = start_size
        self.mesh_size = mesh_size
        # OpenFOAM treats the expansion ratio as the ratio of the largest cell /
        # to smallest cell,
        self.expansion_ratio = self.mesh_size / self.start_size
        if expansion_distance and geometric_ratio:
            raise Exception('Cannot specify both expansion_distance and '
                            'geometric_ratio')
        if geometric_ratio:
            # the geometric ratio is the cell-growth between any two neighbors
            self.geometric_ratio = geometric_ratio
            self.expansion_distance = None
        else:
            # the expansion distance is the % of dim that should be taken by
            # one grading
            self.expansion_distance = expansion_distance * self.dim
            self.geometric_ratio = None
        self.gradings = []
        self.grade_at_midpoint = grade_at_midpoint
        self.grade_start = grade_start
        self.grade_end = grade_end

    @property
    def name(self):
        return 'block_{num}_{axis}_grading'.format(num=self.num, axis=self.axis)

    @property
    def cell_name(self):
        return 'block_{num}_{axis}_cells'.format(num=self.num, axis=self.axis)

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

        return {self.name: self,
                self.cell_name: self.n_cells}

    def __check_interior(self, interior):
        if interior < 0:
            raise Exception(
                'Interior distance for blockGrading {} along axis {} '
                'with dimension ({}mm) cannot be implemented -- grading '
                'starting with size ({}mm) and geometric ratio {} is '
                'larger than dimension! Try increasing geometric_ratio'
                ''.format(self.num, self.axis, self.dim, self.start_size,
                          self.geometric_ratio))

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
        if self.grade_at_midpoint:
            num_gradings += 2

        # create dummy interior grading
        interior = self.dim - num_gradings * geo_dist
        if self.grade_at_midpoint:
            # interior is split
            interior /= 2.
        self.__check_interior(interior)
        interior_n_cells = int(np.ceil(interior / self.last_geo_size(n_steps)))
        interior = grading(interior, interior_n_cells, 1.0)

        # now add gradings

        # start
        if self.grade_start:
            self.gradings.append(expansion.copy())
        # interior #1
        self.gradings.append(interior.copy())
        if self.grade_at_midpoint:
            # contraction / expansion
            self.gradings.append(expansion.copy_with(contraction=True))
            self.gradings.append(expansion.copy())
            # and interior # 2
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


def get_template(filename):
    with open(join('system', '{}.in'.format(filename)), 'r') as file:
        src = Template(file.read())
    return src


def main(mesh_size, wall_normal, geometric_ratio, long_geometric_ratio,
         expansion_distance, upstream_center_line=True):
    # populate mesh dims
    with open(join('system', 'meshDims'), 'w') as file:
        file.write(get_template('meshDims').safe_substitute(mesh_size=mesh_size))

    # get blockMesh
    src = get_template('blockMeshDict')

    # and write to file
    with open(join('system', 'blockMeshDict'), 'w') as file:

        mydict = {}
        graders = []
        # block 0
        graders.append(blockGrader(0, 'y', height, wall_normal, mesh_size,
                                   geometric_ratio, expansion_distance,
                                   upstream_center_line))
        graders.append(blockGrader(0, 'z', L_LE_upstream, wall_normal, mesh_size,
                                   geometric_ratio, expansion_distance, False,
                                   True, False))

        # block 1
        graders.append(blockGrader(1, 'y', D, wall_normal, mesh_size,
                                   geometric_ratio, expansion_distance))
        graders.append(blockGrader(1, 'z', BB_height, wall_normal, mesh_size,
                                   geometric_ratio, expansion_distance))

        # block 2
        graders.append(blockGrader(2, 'y', D, wall_normal, mesh_size,
                                   geometric_ratio, expansion_distance))
        graders.append(blockGrader(2, 'z', BB_height, wall_normal, mesh_size,
                                   geometric_ratio, expansion_distance))

        # block 3
        graders.append(blockGrader(3, 'y', D, wall_normal, mesh_size,
                                   geometric_ratio, expansion_distance))
        graders.append(blockGrader(3, 'z', L_TE_downstream, wall_normal, mesh_size,
                                   long_geometric_ratio, expansion_distance,
                                   grade_start=False))

        # block 4
        graders.append(blockGrader(4, 'y', D, wall_normal, mesh_size,
                                   geometric_ratio, expansion_distance))
        graders.append(blockGrader(4, 'z', L_TE_downstream, wall_normal, mesh_size,
                                   long_geometric_ratio, expansion_distance,
                                   grade_start=False))

        # block 5
        graders.append(blockGrader(5, 'y', D, wall_normal, mesh_size,
                                   geometric_ratio, expansion_distance))
        graders.append(blockGrader(5, 'z', L_TE_downstream, wall_normal, mesh_size,
                                   long_geometric_ratio, expansion_distance,
                                   grade_start=False))

        for grader in graders:
            mydict.update(grader.get_subst_dict())
        file.write(src.safe_substitute(**mydict))


if __name__ == '__main__':
    parser = ArgumentParser('buildMesh.py -- set up blockMeshDict for Volvo '
                            'Flygmotor LES simulation.')
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
                        default=1.03,
                        help='The geometric-ratio of (slow) cell size increases.'
                             'Incompatible with expansion_distance option.')
    parser.add_argument('-e', '--expansion_distance',
                        type=float,
                        default=None,
                        required=False,
                        help='The percent of the dimension dedicated to '
                             'cell-expansion. Incompatible with geometric_ratio '
                             'option.')
    parser.add_argument('-ruc', '--refine_upstream_centerline',
                        dest='upstream_center_line',
                        action='store_true',
                        help='Refine the centerline upstream of the bluff-'
                             'body')
    parser.add_argument('-nruc', '--no_refine_upstream_centerline',
                        dest='upstream_center_line',
                        action='store_false',
                        help='Do not refine the centerline upstream of the bluff-'
                             'body')
    parser.set_defaults(upstream_center_line=True)
    args = parser.parse_args()
    main(args.mesh_size, args.wall_normal, args.geometric_ratio,
         args.long_geometric_ratio, args.expansion_distance,
         args.upstream_center_line)
