import unittest
import argparse as ap
from iris.tests import IrisTest
from .. import serveupimage
from .. import dataproc
from .. import imageproc
from .. import config as conf
import numpy as np
import iris
from numpy.testing import assert_array_equal

import os
fileDir = os.path.dirname(__file__)

class IntegrationTest(unittest.TestCase):
    def setUp(self):
        self.profile = ap.Namespace(**conf.profiles["default"])
        self.data = serveupimage.loadCube(os.path.join(fileDir, "data", "test_input.pp"),
                                          conf.topog_file,
                                          self.profile.data_constraint)
        self.proced_data = iris.load_cube(os.path.join(fileDir, "data", "proced_data.nc"))

    def test_dataproc(self):
        # tidy up any problems arising from the on-the-fly altitude calc
        san_data = dataproc.sanitizeAlt(self.data)
        # regrid and restratify the data
        rg_data = dataproc.regridData(san_data,
                                      regrid_shape=self.profile.regrid_shape,
                                      extent=self.profile.extent)
        # do any further processing (saturation etc) and convert to 8 bit uint
        proced_data = dataproc.procDataCube(rg_data)

        assert_array_equal(self.proced_data.data, proced_data.data)


    def test_image_proc(self):
        data_tiled = imageproc.tileArray(self.proced_data.data,
                                        self.profile.field_width,
                                        self.profile.field_height)
        np.save(os.path.join(fileDir, "data", "tiled_data.npy"), data_tiled)

        # self.assertTrue(np.array_equal(data_tiled))
        

if __name__ == '__main__':
    unittest.main()