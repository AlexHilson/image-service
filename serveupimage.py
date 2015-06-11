#!/usr/bin/env python

import argparse as ap
import iris
import io

from . import dataproc
from . import imageproc
from . import networking
from . import config as conf

"""
serveupimage.py is the top level module for processing
Thredds server data and positing it as an image on the
data service. This includes:

1. Retrieving data from the Thredds server
2. Processing the data of each time slice
3. Converting this processed data to a tiled image
4. Posting the tiled image to the data server

"""

def procTimeSliceToImage(
               data,
               image_dest,
               extent,
               regrid_shape,
               field_width,
               field_height):
    """
    Main processing function. Processes an model_level_number, lat, lon cube,
    including all regridding and restratification of data,
    calculates shadows, and then ultimately posts a tiled
    image to the data service.

    Args:
        * data (iris cube): lat, lon, model_level_number cube 
        * image_dest (str): URL to the data service image destination
        * regrid_shape (tuple): lon, lat, alt dimensions to regrid to
        * field_width (int): image width
        * field_height (int): image height

    """

    # tidy up any problems arising from the on-the-fly altitude calc
    san_data = dataproc.sanitizeAlt(data) 
    # regrid and restratify the data
    rg_data = dataproc.regridData(san_data, regrid_shape=regrid_shape, extent=extent)
    # do any further processing (saturation etc) and convert to 8 bit uints
    proced_data = dataproc.procDataCube(rg_data)

    data_tiled = imageproc.tileArray(proced_data.data)
    shadows_tiled = imageproc.getShadows(data_tiled)

    img_data_out = np.concatenate([data_tiled, shadows_tiled], 2)

    return img_data_out


def procFileToImage(data, profile):
    """
    Wrapper round procTimeSliceToImage which slices over any time dimension
    and parses config settings

    Args:
        * data (cube): cube of data
        * profile (namespace): settings specific to this analysis
            loaded from config.py

    """

    if "altitude" not in [_.name() for _ in data.derived_coords]:
        raise IOError("Derived altitude coord not present - probelm with topography?")
    
    conf_args = (conf.img_data_server,
                 profile.extent,
                 profile.regrid_shape,
                 profile.field_width,
                 profile.field_height)
    
    # if statment to we can accept time, lat, lon, alt data OR lat, lon, alt data
    if len(data.coord("time").points) > 1:
        data.transpose([0, 3, 2, 1]) # change order of axes so that they are the same as the vis
        for time_slice in data.slices_over("time"):
            img_array = procTimeSliceToImage(time_slice, *conf_args)
    else:
        data.transpose([2, 1, 0]) # change order of axes so that they are the same as the vis
        img_array = procTimeSliceToImage(data, *conf_args)

    return img_array


def loadCube(data_file, topog_file, constraint):
    data, topography = iris.load([data_file, topog_file])
    data = data.extract(constraint)

    return data


def parseArgs():
    argparser = ap.ArgumentParser()
    argparser.add_argument("-a", "--profilename", default="default",
        type=str, help="Name of analysis profile settings, as defined in config.py")
    argparser.add_argument("data_file", metavar="file", type=str, help="URI of file to analyse")
    call_args = argparser.parse_args()

    return call_args


if __name__ == "__main__":
    call_args = parseArgs()
    profile = ap.Namespace(**conf.profiles[analysis_profile_name]) # get settings for this type of analysis

    data = loadCube(call_args.data_file, conf.topog_file, profile.constraint)
    img_array = procFileToImage(call_args.profilename, call_args.data_file)

    netowrking.postImage(img_array, data)