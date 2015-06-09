import unittest

import argparse as ap
import datetime
import iris
import requests
import numpy as np
import tempfile
import os

import sys
sys.path.append(".")
import imageproc

import config
modlecon = ap.Namespace(**config.models["UK-V"])

iris.FUTURE.cell_datetime_objects = True

class IntegrationTest(unittest.TestCase):

    def test_makekImage(self):
        imageproc.makeImage(
              modlecon.data_constraint,
              os.path.join(config.thredds_server, "test_data", "synth_cloud_fraction.pp"),
              config.img_data_server,
              extent = modlecon.extent,
              regrid_shape = modlecon.regrid_shape,
              field_width = 4096, field_height = 4096)

if __name__ == '__main__':
    unittest.main()