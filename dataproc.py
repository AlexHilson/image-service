import iris
import numpy as np
import png

import sys
sys.path.append("/Users/niall/Projects/monty/lib/")
import monty.vinterp

from . import config as conf

"""
dataproc.py contains all functions which process the data
including retratification, regridding, rescaling etc.
Called by serveupimage.py

"""

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
    c.data *= conf.max_val
    c.data = np.ma.fix_invalid(c.data, fill_value=conf.max_val)

    return c

if __name__ == "__main__":
    pass