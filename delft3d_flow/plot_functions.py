import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timezone
import netCDF4
import pandas as pd
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
def extract_data_from_output_file(file_path, variable, pattern, depth=1):
    with netCDF4.Dataset(file_path) as nc:
        times = np.array(nc.variables["time"][:])
        if str(pattern[-3]) == "get_depth_index_from_depth":
            depth_index = get_closest_index(depth, np.array(nc.variables["ZK_LYR"][:]) * -1)
            pattern[-3] = depth_index
        data = np.array(nc.variables[variable][pattern])
        data[data == -999] = np.nan
        timestamps = [datetime.utcfromtimestamp(t + (datetime(2008, 3, 1).replace(tzinfo=timezone.utc) - datetime(1970, 1, 1).replace(tzinfo=timezone.utc)).total_seconds()).replace(tzinfo=timezone.utc) for t in times]
        depth = np.array(nc.variables["ZK_LYR"][pattern[-3]])
        x_coor = np.array(nc.variables["XZ"][pattern[-2]][pattern[-1]])
        y_coor = np.array(nc.variables["YZ"][pattern[-2]][pattern[-1]])
        return timestamps, data, (depth, x_coor, y_coor)

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

# %%
def find_closest_date_index(date_array, target_date):
    time_diff = np.abs(np.array(date_array) - target_date)
    closest_index = np.argmin(time_diff)
    return closest_index

# %%
def plot_heatmap(parameters, date_to_plot):
    time_index = find_closest_date_index(parameters[0]["timestamps"], date_to_plot)

    fig = plt.figure(figsize=(18, 8))
    fig.suptitle(parameters[0]["timestamps"][time_index])
    for j in range(len(parameters)):
        plt.subplot(1, len(parameters), j + 1)
        plt.imshow(parameters[j]["data"][time_index], cmap='jet', interpolation='nearest')
        plt.title(parameters[j]["name"])
        plt.colorbar()
    plt.tight_layout()
    plt.show()

# %%
def plot_transect(parameters, date_to_plot):
    time_index = find_closest_date_index(parameters[0]["timestamps"], date_to_plot)

    fig = plt.figure(figsize=(18, 8))
    fig.suptitle(parameters[0]["timestamps"][time_index])
    for j in range(len(parameters)):
        plt.subplot(len(parameters), 1, j + 1)
        plt.imshow(parameters[j]["data"][time_index], cmap='jet', interpolation='nearest', origin='lower')
        plt.title(parameters[j]["name"])
        plt.colorbar()
    plt.tight_layout()
    plt.show()

# %%
def plot_timeseries(parameters):
    fig = plt.figure(figsize=(10, 8))
    fig.suptitle(" x=" + str(parameters[0]['x_coords']) + " y=" + str(parameters[0]['y_coords']) + " depth=" + str(
        parameters[0]['depth']))
    for j in range(len(parameters)):
        plt.subplot(len(parameters), 1, j + 1)
        plt.plot(parameters[j]['timestamps'], parameters[j]['data'])
        plt.title(parameters[j]["name"])
    plt.tight_layout()
    plt.show()

# %%
def plot_xy_heatmap(parameters, date_to_plot):
    time_index = find_closest_date_index(parameters[0]["timestamps"], date_to_plot)
    fig = plt.figure(figsize=(10, 20))
    fig.suptitle(f"Timestamp: {parameters[0]['timestamps'][time_index]}")
    for i, param in enumerate(parameters, start=1):
        x_coords = param['x_coords'].flatten()
        y_coords = param['y_coords'].flatten()
        data_values = param['data'][time_index].flatten()
        df = pd.DataFrame({'X': x_coords, 'Y': y_coords, 'Value': data_values})
        df = df[df['X'] != 0]
        ax = plt.subplot(len(parameters), 1, i)
        scatter = ax.scatter(df['X'], df['Y'], c=df['Value'], cmap='jet', marker='s')
        plt.colorbar(scatter, ax=ax, label='Value')
        plt.title(param['name'])
    plt.tight_layout()
    plt.show()
