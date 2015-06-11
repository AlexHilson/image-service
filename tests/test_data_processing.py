import unittest
import argparse as ap
from iris.tests import IrisTest
from .. import serveupimage
from .. import dataproc
from .. import config as conf
import numpy
from numpy.testing import assert_array_equal

import os
fileDir = os.path.dirname(__file__)

class IntegrationTest(unittest.TestCase):
    def setUp(self):
        self.profile = ap.Namespace(**conf.profiles["default"])
        data_path = os.path.join(fileDir, "data", "test_input.pp")
        self.data = serveupimage.loadCube(data_path,
                                          conf.topog_file,
                                          self.profile.data_constraint)

    def test_dataproc(self):
        for time_slice in self.data.slices_over("time"):
            # tidy up any problems arising from the on-the-fly altitude calc
            san_data = dataproc.sanitizeAlt(time_slice) 
            # regrid and restratify the data
            rg_data = dataproc.regridData(san_data,
                                          regrid_shape=self.profile.regrid_shape,
                                          extent=self.profile.extent)
            # do any further processing (saturation etc) and convert to 8 bit uints
            img_array = serveupimage.procTimeSliceToImage(time_slice,
                                                         conf.img_data_server,
                                                         profile.extent,
                                                         profile.regrid_shape,
                                                         profile.field_width,
                                                         profile.field_height)

        savep = os.path.join(fileDir, "data", "ref_data.pp")
        iris.save(proced_data, savep)

        ref_path = os.path.join(fileDir, "data", "ref_data.pp")
        ref_proced_data = iris.load_cube(ref_path)

        self.assertEqual(ref_proced_data, proced_data)

    def test_image_proc(self):
        pass

if __name__ == '__main__':
    unittest.main()