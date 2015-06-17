#!/usr/bin/env python

import argparse as ap
import iris
import iris.util
import io
import numpy as np
import os
import tempfile

import sys
sys.path.append(".")

import dataproc
import imageproc
import networking
import shadowproc

import config as conf

"""
serveupimage.py is the top level module for processing
Thredds server data and positing it as an image on the
data service. This includes:

1. Retrieving data from the Thredds server
2. Processing the data of each time slice
3. Converting this processed data to a tiled image
4. Posting the tiled image to the data server

"""

def procTimeSliceToImage(data,
                         image_dest,
                         extent,
                         regrid_shape):
    """
    Main processing function. Processes an model_level_number, lat, lon cube,
    including all regridding and restratification of data,
    calculates shadows, and then ultimately posts a tiled
    image to the data service.

    Args:
        * data (iris cube): lat, lon, model_level_number cube 
        * image_dest (str): URL to the data service image destination
        * regrid_shape (tuple): lon, lat, alt dimensions to regrid to

    """

    # tidy up any problems arising from the on-the-fly altitude calc
    san_data = dataproc.sanitizeAlt(data) 
    # regrid and restratify the data
    rg_data = dataproc.regridData(san_data, regrid_shape=regrid_shape, extent=extent)
    # do any further processing (saturation etc) and convert to 8 bit uints
    proced_data = dataproc.procDataCube(rg_data)

    data_tiled = imageproc.tileArray(proced_data.data)
    shadows_tiled = shadowproc.procShadows(data_tiled)

    img_data_out = np.concatenate([data_tiled, shadows_tiled], 2)

    return img_data_out


def loadCube(data_file, topog_file, constraint):
    """
    Loads cube and reorders axes into appropriate structure

    The Iris altitude conversion only works on pp files
    at load time, so we need to pull the nc file from
    OpenDAP, save a local temporary pp file and then
    load in with the topography.

    """
    opendapcube = iris.load_cube(data_file, constraint)
    tempfilep = os.path.join(tempfile.gettempdir(), "temporary.pp")
    iris.save(opendapcube, tempfilep)
    data, topography = iris.load([tempfilep, topog_file])

    if "altitude" not in [_.name() for _ in data.derived_coords]:
        raise IOError("Derived altitude coord not present - probelm with topography?")

    xdim, = data.coord_dims(data.coords(dim_coords=True, axis="X")[0])
    ydim, = data.coord_dims(data.coords(dim_coords=True, axis="Y")[0])
    zdim, = data.coord_dims(data.coords(dim_coords=True, axis="Z")[0])
    try: 
        tdim, = data.coord_dims(data.coords(dim_coords=True, axis="T")[0])
        data.transpose([tdim, xdim, ydim, zdim])
    except IndexError:
        data.transpose([xdim, ydim, zdim])

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
    profile = ap.Namespace(**conf.profiles[call_args.profilename]) # get settings for this type of analysis

    data = loadCube(call_args.data_file, conf.topog_file, profile.data_constraint)

    for time_slice in data.slices_over("time"):
        img_array = procTimeSliceToImage(time_slice,
                                         conf.img_data_server,
                                         profile.extent,
                                         profile.regrid_shape)
        post_object = networking.postImage(img_array, data)