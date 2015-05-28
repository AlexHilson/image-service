import io
import iris
import numpy as np
import png
import requests
import tempfile

iris.FUTURE.cell_datetime_objects = True

DATA_SOURCE = "/Users/niall/Downloads/"
IMAGE_DEST = "http://ec2-52-16-246-202.eu-west-1.compute.amazonaws.com:9000/molab-3dwx-ds/images/"

def get_data_cube(meta_data):
    """
    Retrieves relevant cube of data from the THREADS server.


    """
    c = iris.load_cube(DATA_SOURCE + "cloud_frac.nc", alt_con)[0]
    c.transpose([2, 1, 0]) # change order of axes so that they are the same as the vis
    return c


def proc_data_cube(c):
    """
    Processes data such that it is suitable for visualisation.

    Takes a cube of data, and returns a cube of data values *BETWEEN 0 and 255*
    Other adjustments should be done here, like adjusting range and saturation.
    E.g. for a 15degC potential temperature surface, all values <15 = 0 and >15=255

    """

    c.data *= 255
    return c


def get_post_dict(cube):
    """
    Converts relevant cube metadata into a dictionary of metadata which is compatable
    with the data service.

    """
    payload = {'forecast_reference_time': cube.coord("forecast_reference_time").cell(0).point.isoformat()+".000Z",
               'time' : cube.coord("time").cell(0).point.isoformat()+".000Z",
               'phenomenon' : cube.var_name,
               'data_dimensions': {'x': cube.shape[0], 'y': cube.shape[1], 'z': cube.shape[2]}}
    return payload


def get_shadows(data_cube):
    """
    Calls the shadow service to raymarch light from sun through the data.
    Returns a 3D array of shadow values, the same dimensions as the input.

    Args:
        * data_cube( iris cube ): 3D cube of data
    """

    # CALL GPU CODE HERE #
    return ""


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

    tiled_array = np.zeros([maxx, maxy, maxz])
    datax, datay, dataz = padded_a.shape
    maxitiles = int(maxx/datax)
    maxjtiles = int(maxy/datay)
    tilesperlayer = maxitiles * maxjtiles
    
    for zslice in range(dataz):
        ztile = np.floor(zslice/tilesperlayer)
        ytile = np.floor((zslice - (ztile * tilesperlayer)) / maxitiles)
        xtile = np.mod(zslice - (ztile * tilesperlayer), maxitiles)
        
        try:
            tiled_array[xtile*datax:(xtile+1)*datax,
                     ytile*datay:(ytile+1)*datay,
                     ztile] = padded_a[:, :, zslice]
        except IndexError:
            print "Output array saturated at slice", zslice
            break
            
        
    # swap from row major to column (or vice versa, not sure which way round this is!)
    tiled_array = tiled_array.transpose([1, 0, 2])

    if (tiled_array.shape[0]**0.5)%1 != 0.0 or (tiled_array.shape**0.5)%1 != 0.0:
        raise ValueError("Dimensions for a texture must be square"
                         " numbers i.e. sqrt(n) must be an integer")

    # revese first axis to be compatible with textures which read from top left
    return tiled_array[::-1, ...]

    
def write_png(array, f, height=256, width=256, nchannels=3, alpha="RGB"):
    """
    Writes a tiled array to a png image

    args:
        * array: x, y, rgba array
        * savep: output file
        * height/width: the height/width of the image.
            Must be a square number for use with WebGL
            textures. Need not be equal to each other.

    """
    
    png_writer = png.Writer(height=height, width=width, bitdepth=8, alpha=alpha)
    flat_array = array.reshape(-1, width*nchannels)
    png_writer.write(f, flat_array)


def create_image(meta_data, field_width=4096, field_width=4096):
    """ 
    Retrieves earth science data, processes it, tiles it,
    and finally posts it to the server as an 2D image that 
    can be read by the 3D viz client as a data texture.
    
    Args:
        * meta_data (dict): a dictionary of metadata which
            defines which data to act on
    
    """
    
    cube_in = get_data_cube(meta_data)
    proced_cube_in = proc_data_cube(cube_in)
    data_tiled = tile_array(proced_cube_in.data, maxx=field_width, maxy=field_height, maxz=3, padxy=True)
    
    shadows = get_shadows(proced_cube_in)
    shadows_tiled = tiled_shadows #tile_array(shadows, maxx=4096, maxy=4096, maxz=3, padxy=True)
    
    img_data_out = np.concatenate([data_tiled, shadows_tiled], 2) # join side by side
    
    payload = get_post_dict(cube_in)
    with tempfile.SpooledTemporaryFile(max_size=2e7) as img:
        write_png(img_data_out, img, height=field_width, width=field_width*2, nchannels=3, alpha=False)
        payload['data'] = img
        
        r = requests.post(IMAGE_DEST, payload)