import unittest
from scipy import misc
from .. import shadow_generation as shadowgen
import numpy
from numpy.testing import assert_array_equal

import os
homeDir = os.path.dirname(__file__)

class IntegrationTest(unittest.TestCase):

    def testDrawShadows(self):
    	inPath = os.path.join(homeDir,  'img/cloud_frac_padded_623_812_70_4096_4096.png')
    	outPath = os.path.join(homeDir, 'output/testtmp.png')
    	refPath = os.path.join(homeDir, 'output/ref.png')
        shadowgen.drawShadows(inputFile=inPath,
        						outputFile=outPath)
        outImage = misc.imread(outPath)
        refImage = misc.imread(refPath)
        os.remove(outPath)
        assert_array_equal(outImage, refImage)

if __name__ == '__main__':
    unittest.main()