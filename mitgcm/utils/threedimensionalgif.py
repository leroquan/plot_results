"""

    Comes from : https://git.uwaterloo.ca/tghill/gcmpy/-/tree/master/postprocessing?ref_type=heads

    Create a gif animation and still frame images of slices of a 3D data set.

    Uses netCDF4 files converted from MITgcm binary output (.data) files.
    Automatically creates a .gif animation and saves each frame as a still
    image.

    Parameters:

    Required:
        Name        |   Description
        ------------|-------------------
        var         :   Variable prefix to plot. This is the prefix of the
                        MITgcm binary output files. eg 'T', 'Rho'.

        movie_name  :   Filename to save the gif animation. This works with
                        or without the .gif. extension

        cut_var     :   Axis to take a constant slice of. One of 'x', 'y'
                        or 'z'.

        cut_val     :   Value to take a slice at. Must be a level in the
                        model data.
        ------------|-------------------

    Optional:
        Name                |   Default     |   Description
        --------------------|---------------|--------------------
        data_path           :   '.'         :   Path (absolute or relative) to
                                                the 'data' model configuration
                                                file. Uses 'data' file for
                                                deltaT and startTime fields.

        iters               :   None        :   If None, use all iterations for
                                                matching file names. Otherwise,
                                                can be a list of iteration
                                                numbers. Iterations are
                                                auto zero padded to 10 digits

        vmin                :   None (auto) :   Colour scale min

        vmax                :   None (auto) :   Colour scale max

        image_folder_name   :   PNG_IMAGES  :   Directory to save image files in

        gif_folder_name     :   GIF_IMAGES  :   Directory to save animation in

        image_name          :   None        :   Name to save images as, if given.
                                                The model iteration number is
                                                put before the file
                                                extension. If left as None,
                                                does not save each still frame

        namespec            :   output_{iter}.nc    :   Specifies a file name
                                                        pattern for the .nc
                                                        files

        fps                 :   2           :   Frames per second in the
                                                output .gif animation

        cmap                :'cmocean/thermal':   Colour map for animation

        dpi                 :   200         :   Resolution for still frames

        plot_type           :   'gs'        :   One of None, 'gs', 'contour'
                                                or 'interp'.
                                                None: pcolormesh with no
                                                        shading/interpolation
                                                gs: pcolormesh with
                                                gouraud shading
                                                interp: imshow with
                                                interpolation

        interp_type         :   'bilinear'  :   Interpolation type. See pyplot
                                                imshow documentation
        https://matplotlib.org/api/_as_gen/matplotlib.pyplot.imshow.html

        aspect              :   'auto'      :   One of 'auto' or number.
                                                Auto uses a 4:3 aspect
                                                ratio; Passing a number
                                                forces that aspect ratio


        landmask            :   '#603a17'   :   None or string colour
                                                specification. If given, the
                                                land area is masked with the
                                                specified colour. Default
                                                is brown.

        velocity_field      :   False       :   Flag to show the direction
                                                field overtop of the
                                                pcolor plot. Required fields
                                                'U' and 'V' to be in the
                                                netCDF file

        xstride              :   3           :   stride length in x for picking
                                                data to splot for ice velocity
                                                field. ie, if stride = 3,
                                                only shows every an arrow for
                                                every 3rd data point

        ystride              :   3           :   stride length in y for picking
                                                data to splot for ice velocity
                                                field. ie, if stride = 3,
                                                only shows every an arrow for
                                                every 3rd data point

        zstride              :   3           :   stride length in z for picking
                                                data to splot for ice velocity
                                                field. ie, if stride = 3,
                                                only shows every an arrow for
                                                every 3rd data point

        scale               :   20          :   Scale for ice velocity field
                                                arrow size. A larger scale
                                                means smaller arrows; smaller
                                                scale means larger arrows.

        --------------------|---------------|--------------------
"""

import glob
import os

import numpy as np

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib import animation

import MITgcmutils as mgu

from mitgcm.utils import plotutil, cmaps

defaults = {    'iters':                None,
                'vmin' :                None,
                'vmax' :                None,
                'image_folder_name' :   'PNG_IMAGES',
                'gif_folder_name' :     'GIF_MOVIES',
                'min_points' :          100,
                'namespec' :            'output_{iter}.nc',
                'image_name' :          None,
                'fps' :                 2,
                'cmap' :                'cmocean/thermal',
                'dpi' :                 200,
                'plot_type' :           None,
                'interp_type' :         None,
                'aspect' :              'auto',
                'landmask':             '#603a17',
                'velocity_field':       False,
                'stride':               3,
                'xstride':              None,
                'ystride':              None,
                'zstride':              None,
                'scale' :               20,
                'data_path':            '.',
            }

requireds = ['var', 'movie_name', 'cut_var', 'cut_val', 'sec_per_iter', 'start_time']

def makeanimate(kwargs):
    """Make gif animation and still frames.

    Args is a dictionary containing all arguments specified above. Saves the
    movies and images according to arguments in args.
    """
    args = defaults.copy()
    for key,val in kwargs.items():
        if key in defaults:
            args[key] = val
        elif key in requireds:
            args[key] = val
        else:
            raise KeyError('Unrecognized argument "%s"' % key)    # pre-process iters list to make sure they are 10-digit strings.
    iters = args['iters']
    # if iters is None, find all matching files.
    if iters:
        iters = [str(i).zfill(10) for i in iters]
    else:
        pattern = args['namespec'].replace('{iter}', '*')
        files = glob.glob(pattern)
        iters = sorted([os.path.splitext(f)[0][-10:] for f in files], key = int)

    # deal with directories for .gif and .png; make them if they don't exist
    if not os.path.exists(args['gif_folder_name']):
        os.mkdir(args['gif_folder_name'])
    gifname = os.path.join(args['gif_folder_name'], args['movie_name'])

    if not os.path.exists(args['image_folder_name']):
        os.mkdir(args['image_folder_name'])
    if args['image_name']:
        imgname = os.path.join(args['image_folder_name'], args['image_name'])
    else:
        imgname = None

    # get the grids from the first nc file
    # Raises IOError if the file doesn't exist
    ncdata = plotutil._getdataset(iters[0], args['namespec'])
    X = np.array(ncdata['x'])
    Y = np.array(ncdata['y'])

    # variable 'z' in the netCDF data is just the number of levels
    # variable 'zc' is the vertical coordinate
    Z = np.array(ncdata['z'])
    Zc = np.array(ncdata['zc'])

    cutindex = int(np.where(np.array(ncdata[args['cut_var']]) == args['cut_val'])[0])
    if args['cut_var'] == 'x':
        plotXgrid, plotYgridlevels = np.meshgrid(Y, Z)
        plotYgrid = np.take(Zc, cutindex, axis = 2)
        xlabel = 'y'
        ylabel = 'z'
        cutaxis = 2
    elif args['cut_var'] == 'y':
        plotXgrid, plotYgridlevels = np.meshgrid(X, Z)
        plotYgrid = np.take(Zc, cutindex, axis = 1)
        cutaxis = 1
        xlabel = 'x'
        ylabel = 'z'
    elif args['cut_var'] == 'z':
        plotXgrid, plotYgrid = np.meshgrid(X, Y)
        cutaxis = 0
        xlabel = 'x'
        ylabel = 'y'

    if args['aspect'] == 'auto':
        fig = plt.figure(figsize = (8, 6))
    else:
        C = 6*8
        x = float(np.sqrt(C*args['aspect']))
        y = float(x/args['aspect'])
        fig = plt.figure(figsize=(x, y))

    ax = plt.subplot(111)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    # Already have this file as ncdata variable
    # stillname = _getstillname(iters[0], imgname)
    # initdata = _getdataset(iters[0], args['namespec'])
    # print(initdata.filepath())
    # initvar = np.array(ncdata[args['var']])
    # plotdata_var = np.take(initvar, cutindex, axis = cutaxis)
    plotdata_var = np.take(ncdata[args['var']], cutindex, axis = cutaxis)
    # plotdata_var = np.ma.masked_where(landmask, data)
    cmap = cmaps.getcm(args['cmap'])

    if args['landmask']:
        depth = mgu.rdmds('Depth')
        Nx = len(X)
        Ny = len(Y)
        Nz = len(Z)
        depth = depth.reshape(Ny, Nx)

        """
        The netcdf files put all data points that are below the bottom bed
        at the bottom bed.

        Here I find all the z grid levels and create a new variable
        maskZ with shape (Nz, Ny, Nx) that keeps going below the
        bottom bed.

        If args['landmask'] evaluates as True, then I plot the data against
        this grid, to mask the area below the bottom.
        """
        Z_levels = np.array([np.min(zslice) for zslice in Zc])
        maskZ = np.tile(Z_levels.reshape((len(Z_levels), 1, 1)), (Ny, Nx))

        xy_mins = np.min(Zc, axis = 0)


        if args['cut_var'] == 'x':
            depths = np.take(depth, cutindex, axis = 1)
            depths = np.tile(depths, (Nz, 1))
            zmins = xy_mins[:, cutindex]
            plotYgrid = np.take(maskZ, cutindex, axis = 2)

            landmask = np.abs(plotYgrid) >= depths

        elif args['cut_var'] == 'y':
            depths = np.take(depth, cutindex, axis = 0)
            depths = np.tile(depths, (Nz, 1))

            zmins = xy_mins[cutindex, :]
            plotYgrid = np.take(maskZ, cutindex, axis = 1)


            landmask = np.abs(plotYgrid) >= depths
        else:
            landmask = args['cut_val'] > depth
        cmap.set_bad(args['landmask'], 1)
        plotdata_var = np.ma.masked_where(landmask, plotdata_var)
    # see https://stackoverflow.com/questions/18797175/animation-with-pcolormesh-routine-in-matplotlib-how-do-i-initialize-the-data
    plotdata_var = plotdata_var[:-1, :-1]

    if args['plot_type'] == None:
        pcolor = ax.pcolormesh(plotXgrid, plotYgrid, plotdata_var,
                                cmap = cmap, vmin = args['vmin'],
                                vmax = args['vmax'])
    elif args['plot_type'] == 'gs':
        pcolor = ax.pcolormesh(plotXgrid[:-1, :-1], plotYgrid[:-1, :-1], plotdata_var,
                                cmap = cmap, vmin = args['vmin'],
                                vmax = args['vmax'], shading = 'gouraud')

    elif args['plot_type'] == 'interp':
        pcolor = ax.imshow(plotdata_var, interpolation = args['interp_type'],
                        extent = [plotXgrid[0,0], plotXgrid[-1, -1],
                                    plotYgrid[0, 0], plotYgrid[-1, -1]],
                        cmap = cmap, vmin = args['vmin'],
                        vmax = args['vmax'], origin = 'lower',
                        aspect = 'auto')

    if args['velocity_field']:
        if args['cut_var']=='x':
            xwind = 'V'
            ywind = 'W'
            xst = args['ystride'] if args['ystride'] else args['stride']
            yst = args['zstride'] if args['zstride'] else args['stride']
        elif args['cut_var'] == 'y':
            xwind = 'U'
            ywind = 'W'
            xst = args['xstride'] if args['xstride'] else args['stride']
            yst = args['zstride'] if args['zstride'] else args['stride']
        else:
            xwind = 'U'
            ywind = 'V'
            xst = args['xstride'] if args['xstride'] else args['stride']
            yst = args['ystride'] if args['ystride'] else args['stride']
        U = np.array(ncdata[xwind])
        V = np.array(ncdata[ywind])
        U = np.take(U, cutindex, axis = cutaxis)
        V = np.take(V, cutindex, axis = cutaxis)

        U = U[::yst, ::xst]
        V = V[::yst, ::xst]
        quiverplot = ax.quiver(plotXgrid[::yst, ::xst], plotYgrid[::yst, ::xst], U, V,
                                pivot ='mid', scale = args['scale'])

    plt.tight_layout()

    def animate(iter):
        if imgname:
            stillname = plotutil._getstillname(iter, imgname)
        else:
            stillname = None
        try:
            iterdata = plotutil._getdataset(iter, args['namespec'])

            print("Plotting file %s" % iterdata.filepath())
            plotdata_var = np.take(iterdata[args['var']], cutindex, axis = cutaxis)
            if args['landmask']:
                plotdata_var = np.ma.masked_where(landmask, plotdata_var)
            plotdata_var = plotdata_var[:-1, :-1]

            plotdata = plotdata_var if args['plot_type'] == 'interp' \
                            else plotdata_var.ravel()
            pcolor.set_array(plotdata)

            time = int(iter)*args['sec_per_iter']
            title = '{var} at {cut_var}={cut_val} at t=%s' % time
            title = title.format(var=args['var'], cut_var=args['cut_var'], cut_val=args['cut_val'])
            ax.set_title(title)

            if args['velocity_field']:
                iter_U = np.take(iterdata[xwind], cutindex, axis = cutaxis)
                iter_V = np.take(iterdata[ywind], cutindex, axis = cutaxis)
                U = iter_U[::yst, ::xst]
                V = iter_V[::yst, ::xst]
                quiverplot.set_UVC(U, V)

            plotutil._adjustsubplots(fig)
            iterdata.close()
            if stillname:
                fig.savefig(stillname, dpi = args['dpi'])

        except IOError: # means netCDF file couldn't be opened
            print("Skipping iter %s (unable to open)" % iter)

        except IndexError as ie: # means a variable couldn't be read
            print("Skipping iter %s (Error: %s)"%(iter, ie))
            # Close the file if it could be opened but not a variable
            iterdata.close()

        finally:
            returnval = (pcolor, quiverplot) if args['velocity_field'] else pcolor
            return returnval

    fig.colorbar(pcolor)

    anim = animation.FuncAnimation(fig, animate, frames = iters,
                        blit = False, repeat = False)

    gifwriter = animation.ImageMagickFileWriter(fps = args['fps'])
    anim.save(gifname, writer = gifwriter)

    if args['image_name']:
        print("Saved still frames in %s" % args['image_folder_name'])
    print("Saved animation as %s" % gifname)
