import argschema
from .schemas import SolverSchema
from .data_handler import DataLoader
from .transform.transform import Transform
import numpy as np
import scipy

example1 = {
        'output_json': '/allen/programs/celltypes/workgroups/em-connectomics/danielk/em_coregistration/transform.json',
        'data': {
            'landmark_file': './data/17797_2Pfix_EMmoving_20191010_1652_piecewise_trial_updated_Master.csv',
            'header': ['label', 'flag', 'emx', 'emy', 'emz', 'optx', 'opty', 'optz'],
            'actions': ['invert_opty'],
            'sd_set': {'src': 'em', 'dst': 'opt'}
        },
        "transform": {
            'name': 'PolynomialModel',
            'order': 1
            }
        }

example2 = {
        'output_json': '/allen/programs/celltypes/workgroups/em-connectomics/danielk/em_coregistration/transform.json',
        'data': {
            'landmark_file': './data/17797_2Pfix_EMmoving_20191010_1652_piecewise_trial_updated_Master.csv',
            'header': ['label', 'flag', 'emx', 'emy', 'emz', 'optx', 'opty', 'optz'],
            'actions': ['invert_opty', 'em_nm_to_neurog'],
            'sd_set': {'src': 'opt', 'dst': 'em'}
        },
        "transform": {
            'name': 'PolynomialModel',
            'order': 1,
                }
        }


def control_pts_from_bounds(data, npts, bounds_buffer=0):
    """create thin plate spline control points
    from the bounds of provided data.

    Parameters
    ----------
    data : :class:`numpy.ndarray`
        ndata x 3 Cartesian coordinates of data.
    npts : list
        [nx, ny, nz]
        number of control points per axis. total
        number of control points will be nx * ny * nz

    Returns
    -------
    control_pts : :class:`numpy.ndarray`
        npts^3 x 3 Cartesian coordinates of controls.

    """
    x, y, z = [
            np.linspace(
                data[:, i].min() - bounds_buffer,
                data[:, i].max() + bounds_buffer,
                npts[i])
            for i in [0, 1, 2]]
    xt, yt, zt = np.meshgrid(x, y, z)
    control_pts = np.vstack((
        xt.flatten(),
        yt.flatten(),
        zt.flatten())).transpose()
    return control_pts


def leave_out(data, index):
    if index is None:
        return data, None
    else:
        keep = np.ones(data['labels'].size).astype(bool)
        keep[index] = False
        kdata = {
                'src': data['src'][keep],
                'dst': data['dst'][keep],
                'labels': data['labels'][keep]
                }
        keep = np.invert(keep)
        ldata = {
                'src': data['src'][keep],
                'dst': data['dst'][keep],
                'labels': data['labels'][keep]
                }
        return kdata, ldata


class Solve3D(argschema.ArgSchemaParser):
    """class to solve a 3D coregistration problem"""
    default_schema = SolverSchema

    def run(self, control_pts=None):
        """run the solve

        Parameters
        ----------
        control_pts : :class:`numpy.ndarray`
            user-supplied ncntrl x 3 Cartesian coordinates
            of control points. default None will create
            control points from bounds of input data.

        """
        d = DataLoader(input_data=self.args['data'], args=[])
        d.run()
        self.data = d.data

        self.data, self.left_out = leave_out(self.data, self.args['leave_out_index'])

        self.transform = Transform(json=self.args['transform'])

        self.transform.estimate(self.data['src'], self.data['dst'])

        self.residuals = (
                self.data['dst'] -
                self.transform.tform(self.data['src']))

        print('average residual [dst units]: %0.4f' % (
            np.linalg.norm(self.residuals, axis=1).mean()))

        self.output(self.transform.to_dict(), indent=2)


if __name__ == '__main__':  # pragma: no cover
    smod = Solve3D(input_data=example1)
    smod.run()
    smod = Solve3D(input_data=example2)
    smod.run()
