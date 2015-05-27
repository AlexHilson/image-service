"""
This module converts 3D (x, y, z) numpy arrays of data tiles (x, y) of data
in png files. These can then be read as WebGL textures.

The z dimension is deconstructed and the component x, y data is tiled as follows:
Columns, then rows, then channel (increasing through R, G, B, A). Note that
the RGBA values are unrelated to colors or alpha, they are merely data
channels.


Example usage:

import iris
d = iris.load_cube("cloud_frac.nc")
array_to_png(d.data*255, "cloud_frac_623_812_70_4096_4096.png", width=4096, height=4096)

"""

from __future__ import division
import png
import numpy as np

def tile_array(a, maxx=256, maxy=256, maxz=3, padxy=True):
    """
    Flattens an x,y,z 3D array into an array of x,y tiles
    
    Tiling order is column, followed by row, followed by channel
    
    Note that png textures coordinates increase top left to
    bottom right so we also need to take this into account.
    
    Args:
        * a (numpy array): a 3d numpy array of data
        * max<xyz> (int): the limits of the image size in pixels.
            NB that maxz is either 1 (Grayscale), 3 (RGB) or 4 (RGBA)
        
    This could be made more efficient using stride tricks
    
    """
    
    if padxy:
        padded_a = np.zeros([a.shape[0]+2, a.shape[1]+2, a.shape[2]])
        padded_a[1:-1, 1:-1, :] = a
    else:
        padded_a = a

    pngarray = np.zeros([maxx, maxy, maxz])
    datax, datay, dataz = padded_a.shape
    maxitiles = int(maxx/datax)
    maxjtiles = int(maxy/datay)
    tilesperlayer = maxitiles * maxjtiles
    
    for zslice in range(dataz):
        ztile = np.floor(zslice/tilesperlayer)
        ytile = np.floor((zslice - (ztile * tilesperlayer)) / maxitiles)
        xtile = np.mod(zslice - (ztile * tilesperlayer), maxitiles)
        
        try:
            pngarray[xtile*datax:(xtile+1)*datax,
                     ytile*datay:(ytile+1)*datay,
                     ztile] = padded_a[:, :, zslice]
        except IndexError:
            print "Output array saturated at slice", zslice
            break
            
        
    pngarray = pngarray.transpose([1, 0, 2]) # swap from row major to column (or vice versa, not sure which way round this is!)

    return pngarray[::-1, ...] # revese first axis to be compatible with textures

    
def write_png(array, savep, height=256, width=256, nchannels=3, alpha="RGB"):
    """
    Writes a tiled array to a png image

    args:
        * array: x, y, rgba array
        * savep: output file
        * height/width: the height/width of the image.
            Must be a square number for use with WebGL
            textures. Need not be equal to each other.

    """
    
    if (height**0.5)%1 != 0.0 or (width**0.5)%1 != 0.0:
        raise ValueError("Dimensions must be square numbers i.e. sqrt(n) must be an integer")
    
        png_writer = png.Writer(height=height, width=width, bitdepth=8, alpha=alpha)
        with open(savep, 'wb') as f:
            flat_array = array.reshape(-1, width*n_channels) #assuming RGB i.e. 3 channels
            png_writer.write(f, flat_array)
        

def array_to_png(data, filename, height=256, width=256, padxy=True):
    """ Converts a x,y,z 3D array to a tiled png image """
    tiled_array = tile_array(data, maxx=height, maxy=width, maxz=3, padxy=padxy)
    write_png(tiled_array, filename, height, width)