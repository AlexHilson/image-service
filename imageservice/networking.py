import iris
import requests
import tempfile
import os
import tempfile

import sys
sys.path.append(".")
import imageproc
import config as conf

"""
newtorking.py contains all the function that deal with
posting to the data service. Called by serveupimage.py

"""

def getPostDict(cube, mime_type="image/png"):
    """
    Converts relevant cube metadata into a dictionary of metadata which is compatable
    with the data service.

    """
    with iris.FUTURE.context(cell_datetime_objects=True):
        payload = {'forecast_reference_time': cube.coord("forecast_reference_time").cell(0).point.isoformat()+".000Z",
                   'forecast_time' : cube.coord("time").cell(0).point.isoformat()+".000Z",
                   'phenomenon' : 'cloud_fraction_in_a_layer',#cube.var_name,
                   'mime_type' : mime_type,
                   'model' : 'uk_v'}#,
                   # 'data_dimensions': {'x': cube.shape[0], 'y': cube.shape[1], 'z': cube.shape[2]}}
        return payload


def postImage(img_data, data, field_width, field_height):
    """
    Sends the data to the data service via a post

    Args:
        * img_data(np.Array): Numpy array of i x j x channels
        * data (cube): The cube metadata is used for the post
            metadata
    """
    tempfilep = os.path.join(tempfile.gettempdir(), "temp.png")
    with open(tempfilep, "wb") as img:
        imageproc.writePng(img_data, img,
                  height=field_height, width=field_width*2,
                  nchannels=3, alpha=False)
    payload = getPostDict(data)
    try:
        with open(tempfilep, "rb") as img:
            r = requests.post(conf.img_data_server, data=payload, files={"data": img})
        if r.status_code != 201:
            raise IOError(r.status_code, r.text)
    finally:
        os.remove(tempfilep)