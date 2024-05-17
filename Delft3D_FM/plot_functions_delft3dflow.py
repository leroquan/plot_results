import numpy as np
from datetime import datetime, timezone
import netCDF4
import sys

def get_closest_index(value, array):
    array = np.asarray(array)
    sorted_array = np.sort(array)
    if len(array) == 0:
        raise ValueError("Array must be longer than len(0) to find index of value")
    elif len(array) == 1:
        return 0
    if value > (2 * sorted_array[-1] - sorted_array[-2]):
        raise ValueError("Value {} greater than max available ({})".format(value, sorted_array[-1]))
    elif value < (2 * sorted_array[0] - sorted_array[-1]):
        raise ValueError("Value {} less than min available ({})".format(value, sorted_array[0]))
    return (np.abs(array - value)).argmin()

# %%
def get_closest_index_by_coord(x_array, y_array, x_coor, y_coor):
    min_distance = sys.maxsize
    closest_index = None

    # Iterate through each cell in the grid
    for n in range(len(x_array)):
        for m in range(len(x_array[0])):
            # Calculate distance to the given coordinate
            distance = (x_array[n][m] - x_coor) ** 2 + (y_array[n][m] - y_coor) ** 2
            if distance < min_distance:
                min_distance = distance
                closest_index = (n, m)

    return closest_index

# %%
def extract_timeseries_from_output_file_by_coordinates(file_path, variable, pattern, x_coor, y_coor, depth):
    with netCDF4.Dataset(file_path) as nc:
        coor_index = get_closest_index_by_coord(np.array(nc.variables["XZ"][:]), np.array(nc.variables["YZ"][:]),
                                                x_coor, y_coor)
        pattern[-2] = coor_index[0]
        pattern[-1] = coor_index[1]
        depth_index = get_closest_index(depth, np.array(nc.variables["ZK_LYR"][:]) * -1)
        pattern[-3] = depth_index
        times = np.array(nc.variables["time"][:])
        data = np.array(nc.variables[variable][pattern])
        data[data == -999] = np.nan
        timestamps = [datetime.utcfromtimestamp(t + (
                    datetime(2008, 3, 1).replace(tzinfo=timezone.utc) - datetime(1970, 1, 1).replace(
                tzinfo=timezone.utc)).total_seconds()).replace(tzinfo=timezone.utc) for t in times]
        depth_plot = np.array(nc.variables["ZK_LYR"][pattern[-3]])
        x_coor_plot = np.array(nc.variables["XZ"][pattern[-2]][pattern[-1]])
        y_coor_plot = np.array(nc.variables["YZ"][pattern[-2]][pattern[-1]])
        return timestamps, data, (depth_plot, x_coor_plot, y_coor_plot)



