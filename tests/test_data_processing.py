import unittest
import argparse as ap
from iris.tests import IrisTest
from .. import serveupimage
from .. import dataproc
from .. import imageproc
from .. import shadowproc
from .. import networking
from .. import config as conf
import numpy as np
import iris
from numpy.testing import assert_array_equal

import os
fileDir = os.path.dirname(__file__)

class UnitTests(unittest.TestCase):
    def setUp(self):
        self.profile = ap.Namespace(**conf.profiles["default"])
        self.data = serveupimage.loadCube(os.path.join(fileDir, "data", "test_input.pp"),
                                          conf.topog_file,
                                          self.profile.data_constraint)
        self.proced_data = iris.load_cube(os.path.join(fileDir, "data", "proced_data.nc"))
        self.tiled_data = iris.load_cube(os.path.join(fileDir, "data", "tiled_data.nc")).data
        self.tiled_shadows = iris.load_cube(os.path.join(fileDir, "data", "tiled_data.nc")).data

    def test_dataproc(self):
        # tidy up any problems arising from the on-the-fly altitude calc
        san_data = dataproc.sanitizeAlt(self.data)
        # regrid and restratify the data
        rg_data = dataproc.regridData(san_data,
                                      regrid_shape=self.profile.regrid_shape,
                                      extent=self.profile.extent)
        # do any further processing (saturation etc) and convert to 8 bit uint
        proced_data = dataproc.procDataCube(rg_data)

        self.assertTrue(proced_data.data.max() <= conf.max_val)
        assert_array_equal(self.proced_data.data, proced_data.data)

    def test_imageproc(self):
        data_tiled = imageproc.tileArray(self.proced_data.data,
                                        self.profile.field_width,
                                        self.profile.field_height)

        assert_array_equal(self.tiled_data, data_tiled)

    def test_shadowproc(self):
        tiled_shadows = shadowproc.procShadows(self.tiled_data)
        import scipy
        import scipy.misc
        scipy.misc.imsave("./testimg.png", tiled_shadows)
        _ = iris.cube.Cube(tiled_shadows)
        iris.save(_, os.path.join(fileDir, "data", "tiled_shadows.nc"))

    def test_networking(self):
        img_out = np.concatenate([self.tiled_data, self.tiled_shadows], 1)
        networking.postImage(img_out,
                             self.data,
                             self.profile.field_width,
                             self.profile.field_height)

        

if __name__ == '__main__':
    unittest.main()