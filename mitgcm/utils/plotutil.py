"""

    module plotutil.py

    Module providing helper functions to the plotting modules.

    Comes from : https://git.uwaterloo.ca/tghill/gcmpy/-/tree/master/postprocessing?ref_type=heads

"""

import os

import netCDF4


def _getdataset(iter, namespec):
    """Helper function to return the netCDF4 Dataset object corresponding
    to iteration iter, with name format namespec
    """
    ncfilename = namespec.format(iter=iter)
    try:
        ncdata = netCDF4.Dataset(ncfilename, 'r')
    except:
        raise IOError("Unable to open netCDF4 file %s" % ncfilename)
    return ncdata

def _getstillname(iter, pngname):
    """Helper function to name the individual png frames with the iteration
    """
    stillname, stillext = os.path.splitext(pngname)
    return ''.join([stillname, iter, stillext])

def _adjustsubplots(fig):
    """Helper function to set the spacing around the figure to make
    sure no axes or titles are cut off
    """
    fig.subplots_adjust(bottom = 0.15, top = 0.9, left = 0.15, right = 0.975)
