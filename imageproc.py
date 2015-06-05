import io
import iris
import numpy as np
import png
import requests
import tempfile

import sys
sys.path.append("/Users/niall/Projects/monty/lib/")
import monty.vinterp

MAX_VAL = 255


################# Loading data ###############################

def getTopographyFile():
    """
    Gets a topography file for the correct area

    """ 
    return "/Users/niall/Data/ukv/ukv_orog.pp"


def loadData(loadConstraint, dataFile):
    """
    Loads data along with its topography file in order for Iris to calculate the
    altitude derived coord

    """
    c = iris.load_cube([dataFile, getTopographyFile()], loadConstraint)
    c.transpose([2, 1, 0]) # change order of axes so that they are the same as the vis

    if [_.name() for _ in c.dim_coords] != [ "grid_longitude", "grid_latitude", "model_level_number" ]:
        raise IOError("Loaded cube did not have the expected dimensions")
    if "altitude" not in [_.name() for _ in c.derived_coords]:
        raise IOError("Derived altitude coord not created - probelm with topography?")

    return c

############## Data processing ####################

def sanitizeAlt(c, sea_level=3):
    """
    Takes a cube and sanitizes the altitude coordinates,
    including removing negative values or NaNs, and adding
    a log_altitude coordinate, which will be used for the
    restratifying.

    """
    sanitized_alt = c.coord("altitude").points
    sanitized_alt[np.logical_not(np.isfinite(sanitized_alt))] = sea_level
    sanitized_alt[sanitized_alt < sea_level] = sea_level
    logaltcoord = iris.coords.AuxCoord(np.log(sanitized_alt), long_name="log_altitude")
    c.add_aux_coord(logaltcoord, [0, 1, 2])

    return c


def restratifyAltLevels(c, nalt):
    """
    Restratifies the cube into nalt levels linearly spaced
    between the original min and max alt

    """
    log_levs = np.linspace(c.coord("log_altitude").points.min(),
                              c.coord("log_altitude").points.max(),
                              nalt)
    alt_axis, = c.coord_dims("model_level_number")
    restratified_data = monty.vinterp.interpolate(log_levs,
                                                    c.coord("log_altitude").points,
                                                    c.data,
                                                    axis=alt_axis,
                                                    extrapolation=monty.vinterp.EXTRAPOLATE_NAN,
                                                    interpolation=monty.vinterp.INTERPOLATE_LINEAR)

    restratified_data_cube = c[:, :, :nalt].copy(data=np.ma.masked_invalid(restratified_data))
    restratified_data_cube.remove_coord("model_level_number")
    restratified_data_cube.remove_coord("sigma")
    restratified_data_cube.remove_coord("level_height")
    restratified_data_cube.remove_aux_factory(restratified_data_cube.aux_factories[0])

    restratified_data_cube.coord("grid_latitude").guess_bounds()
    restratified_data_cube.coord("grid_longitude").guess_bounds()

    alt_coord = iris.coords.DimCoord(np.exp(log_levs), long_name="altitude", units="m")
    restratified_data_cube.add_dim_coord(alt_coord, alt_axis)
    
    return restratified_data_cube


def horizRegrid(c, nlat, nlon, extent):
    """
    Takes a cube (in any projection) and regrids it onto a
    recatilinear nlat x nlon grid spaced linearly between

    """
    u = iris.unit.Unit("degrees")
    cs = iris.coord_systems.GeogCS(iris.fileformats.pp.EARTH_RADIUS)

    lonc = iris.coords.DimCoord(np.linspace(extent[0], extent[1], nlon),
                                    standard_name="longitude",
                                    units=u,
                                    coord_system=cs)
    lonc.guess_bounds()

    latc = iris.coords.DimCoord(np.linspace(extent[2], extent[3], nlat),
                                    standard_name="latitude",
                                    units=u,
                                    coord_system=cs)
    latc.guess_bounds()

    grid_cube = iris.cube.Cube(np.empty([nlat, nlon]))
    grid_cube.add_dim_coord(latc, 0)
    grid_cube.add_dim_coord(lonc, 1)
    
    rg_c = c.regrid(grid_cube, iris.analysis.Linear(extrapolation_mode='mask'))
    
    return rg_c

def trimOutsideDomain(c):
    """
    When we regrid from polar stereographic to rectalinear, the resultant
    shape is non-orthogonal, and is surrounded by masked values. This
    function trims the cube to be an orthogonal region of real data.

    Its a little bespoke and make be unscescesarry if we can swith
    to an AreaWeighted function.

    """
    # assess the top layer as its likely to be free
    # of values that are maksed for terrain.
    lonmean = np.mean(c[:, :, -1].data.mask, axis=1)
    glonmean = np.gradient(lonmean)
    uselat = (lonmean < 1.0) & (np.fabs(glonmean) < 0.004)

    latmean = np.mean(c[:, :, -1].data.mask, axis=0)
    glatmean = np.gradient(latmean)
    uselon = (latmean < 1.0) & (np.fabs(glatmean) < 0.004)

    return c[uselat, uselon, :]


def regridData(c, regrid_shape, extent):
    """
    Regrids a cube onto a nalt x nlat x nlon recatlinear cube
    """
    c = restratifyAltLevels(c, regrid_shape[2])
    c = horizRegrid(c, regrid_shape[1], regrid_shape[0], extent)
    # remove the to latyer which seems to artificially masked from regridding
    c = trimOutsideDomain(c[:, :, :-1])

    if np.isnan(c.data.compressed().mean()):
        raise ValueError("Regridded data is NaN - are the lat/lon ranges compatable?")

    return c


def procDataCube(c):
    """
    Processes data such that it is suitable for visualisation.

    Takes a cube of data, and returns a cube of data values *BETWEEN 0 and MAX_VAL (e.g. 255)*
    Other adjustments should be done here, like adjusting range and saturation.
    E.g. for a 15degC potential temperature surface, all values <15 = 0 and >15=255

    NB that all masked values will also be converted to MAX_VAL.

    """
    c.data *= MAX_VAL
    c.data = np.ma.fix_invalid(c.data, fill_value=MAX_VAL)

    return c


################ Calculate shadows ######################## 

def getShadows(data_cube):
    """
    Calls the shadow service to raymarch light from sun through the data.
    Returns a 3D array of shadow values, the same dimensions as the input.

    Args:
        * data_cube( iris cube ): 3D cube of data
    """

    # CALL GPU CODE HERE #
    return data_cube


################ Output image #############################

def tileArray(a, maxx=4096, maxy=4096, maxz=3, padxy=True):
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

    if (tiled_array.shape[0]**0.5)%1 != 0.0 or (tiled_array.shape[1]**0.5)%1 != 0.0:
        raise ValueError("Dimensions for a texture must be square"
                         " numbers i.e. sqrt(n) must be an integer")

    # revese first axis to be compatible with textures which read from top left
    return tiled_array[::-1, ...]

    
def writePng(array, f, height=4096, width=4096, nchannels=3, alpha="RGB"):
    """
    Writes a tiled array to a png image

    args:
        * array: x, y, rgba array
        * savep: output file
        * height/width: the height/width of the image.
            Must be a square number for use with WebGL
            textures. Need not be equal to each other.

    """
    
    png_writer = png.Writer(height=height, width=width, bitdepth=8, alpha=alpha, colormap=True)
    flat_array = array.reshape(-1, width*nchannels)
    png_writer.write(f, flat_array)


############ post data #################

    def getPostDict(cube, mime_type="image/png"):
        """
        Converts relevant cube metadata into a dictionary of metadata which is compatable
        with the data service.

        """
        with iris.FUTURE.context(cell_datetime_objects=True):
            payload = {'forecast_reference_time': cube.coord("forecast_reference_time").cell(0).point.isoformat()+".000Z",
                       'forecast_time' : cube.coord("time").cell(0).point.isoformat()+".000Z",
                       'phenomenon' : cube.var_name,
                       'mime_type' : mime_type,
                       'model' : 'uk_v'}#,
                       # 'data_dimensions': {'x': cube.shape[0], 'y': cube.shape[1], 'z': cube.shape[2]}}
            return payload

############### main function ###############
def makeImage(loadConstraint,
               dataFile,
               image_dest,
               extent,
               regrid_shape = [400, 400, 35],
               field_width = 4096, field_height = 4096):

    data = loadData(loadConstraint, dataFile)

    san_data = sanitizeAlt(data)
    rg_data = regridData(san_data, regrid_shape=regrid_shape, extent=extent)
    proced_data = procDataCube(rg_data)
    shadows = getShadows(proced_data)

    data_tiled = tileArray(proced_data.data)
    shadows_tiled = tileArray(shadows.data)

    img_data_out = np.concatenate([data_tiled, shadows_tiled], 2)
    # with tempfile.SpooledTemporaryFile(max_size=2e7) as img:
    with open("temp.png", "wb") as img:
        writePng(img_data_out, img,
                  height=field_height, width=field_width*2,
                  nchannels=3, alpha=False)
    payload = getPostDict(data)
    with open("temp.png", "rb") as img:
        payload["data"] = img
        r = requests.post(image_dest, payload)
        if r.status_code != 201:
            raise IOError(r.status_code, r.text)