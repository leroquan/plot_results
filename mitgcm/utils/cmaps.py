"""
    Comes from : https://git.uwaterloo.ca/tghill/gcmpy/-/tree/master/postprocessing?ref_type=heads

    cmaps.py

    Module for loading colourmaps for MITgcm post-processing.

    Some colourmaps live in Matplotlib, and some live in external
    packages like cmocean. This module searches all available packages
    for a colourmap name, and returns the colourmap instance.

"""

# To import packages from their string names
import importlib

# For matplotlib colourmaps
import matplotlib

external_packages = ['cmocean.cm',]

aliases = { 'cmocean'       :   'cmocean.cm',
            'matplotlib'    :   'matplotlib.cm',
        }

def _cmap_from_pkg(package, name):
    """Returns a colourmap from the specified package.

    Inputs:
     *  name: String giving the name of the colourmap
     *  package: a module object to import the colourmap from
    """
    try:
        cmap = getattr(package, name)
    except:
        raise NameError('No colourmap named %s in package %s' % (name, package))
    return cmap

def getcm(name):
    """getcm returns a matplotlib colormap instance from a colormap name

    If name is specified as package/name, it will specifically use package's
    colourmap of name.

    Otherwise, all available packages are searched until a matching
    name is found, in hierarchy:

        1   ::  Matplotlib.cm
        2   ::  All available external packages:
                a   ::  cmocean

    If name is a matplotlib.colors.LinearSegmentedColormap, the colourmap
    is passed to the plotting fucntions.

    Inputs:
     *  name:   String name specififying a colourmap, or a colourmap instance.
                The string should be specified as either "cmap" or
                "package/cmap", where package optionally specifies which
                package to look in to find the colourmap cmap.

    Returns:
     *  A matplotlib.colors.LinearSegmentedColormap instance

    Raises:
     *  NameError if the given colourmap can't be found in any package.
    """
    pkglist = ['matplotlib.cm'] + external_packages
    if type(name) is matplotlib.colors.LinearSegmentedColormap:
        return name
    package, name = name.split('/') if '/' in name else (None, name)
    package = aliases[package] if package in aliases else package

    if package:
        cmodule = importlib.import_module(package)
        cmap = _cmap_from_pkg(cmodule, name)

    else:
        for module in pkglist:
            cmodule = importlib.import_module(module)
            try:
                cmap = _cmap_from_pkg(cmodule, name)
                break
            except NameError:
                continue
        else:
            raise NameError('Colourmap %s not found in packages %s' % (name, pkglist))

    return cmap

if __name__ == '__main__':
    print('jet:', getcm('jet'))
    print('Spectral_r:', getcm('/Spectral_r'))
    print('cmocean/ice:', getcm('cmocean/ice'))
    print('ice:', getcm('ice'))
