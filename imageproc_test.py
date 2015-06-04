import unittest

import datetime
import iris
import requests
import numpy as np
import tempfile
import os

import sys
sys.path.append(".")
import imageproc

iris.FUTURE.cell_datetime_objects = True

THREDDS_SERVER =  "/Users/niall/Data/PretendTHREDDS/"
DATA_SERVER = "http://ec2-52-16-246-202.eu-west-1.compute.amazonaws.com:9000/molab-3dwx-ds/images/"

class IntegrationTest(unittest.TestCase):

    def test_makekImage(self):
        levcon = iris.Constraint(model_level_number=lambda v: v.point < 60)

        imageproc.makeImage(
              levcon,
              os.path.join(THREDDS_SERVER, "test_data", "synth_cloud_fraction.pp"),
              DATA_SERVER,
              max_lat = 60.866, min_lat = 47.924, max_lon = 6.406, min_lon = -13.62,
              field_width = 4096, field_height = 4096)

if __name__ == '__main__':
    unittest.main()