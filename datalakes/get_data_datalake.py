from datetime import datetime
import os

import xarray as xr
import numpy as np
import json

from collections import defaultdict

import sys
parent_dir = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.append(parent_dir)
from utils import try_download


def parse_nc_datalakes_from_folder(folder_path: str) -> xr.Dataset:
    nc_files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith('.nc')]

    if not nc_files:
        raise FileNotFoundError(f"No NetCDF files found in directory {folder_path}")

    combined_dataset = xr.open_mfdataset(nc_files, combine='by_coords')

    return combined_dataset


def datalakes_select_from_depth(dataset: xr.Dataset, variable: str, given_depth: float) -> xr.DataArray:
    closest_depth = dataset.depth.sel(depth=given_depth, method='nearest')

    return dataset[variable].sel(depth=closest_depth)


def datalakes_select_profile(dataset: xr.Dataset, variable: str, given_time: datetime) -> xr.DataArray:
    closest_time = dataset.time.sel(time=given_time, method='nearest')

    return dataset[variable].sel(time=closest_time)


def get_ids_files_filtered_by_dates(files_properties, start_date: datetime, end_date: datetime) -> list[int]:
    file_ids = []
    for file in files_properties:
        if file['mindatetime'] is None or file['maxdatetime'] is None:
            continue
        min_date = datetime.fromisoformat(file['mindatetime'].replace('Z', '+00:00'))
        max_date = datetime.fromisoformat(file['maxdatetime'].replace('Z', '+00:00'))
        if min_date > start_date and min_date < end_date:
            file_ids.append(file['id'])
            continue
        if max_date < end_date and max_date > start_date:
            file_ids.append(file['id'])
            continue

    if len(file_ids) == 0:
        raise FileNotFoundError(f"No data between date {start_date} and {end_date} found in {files_properties}")

    return file_ids


def get_ids_files_filtered_by_datatype(files_properties: json, datatype: str) -> list[int]:
    file_ids = []
    for file in files_properties:
        if file['filetype'] == datatype:
            file_ids.append(file['id'])

    if len(file_ids) == 0:
        raise FileNotFoundError(f"No data of type {datatype} found in {files_properties}")

    return file_ids


def parse_from_thermochain(json_data: json):
    meas_data = xr.Dataset(
        {
            'temp': (['depth', 'time'], np.array(json_data['z'], dtype='float'))
        },
        coords={
            'time': np.array(json_data['x'], dtype='datetime64[s]').astype('datetime64[ns]'),
            'depth': -1 * np.array(json_data['y'], dtype='float')
        }
    )

    return meas_data


def handle_duplicates(json_data: json):
    adjusted_y = []
    seen = defaultdict(int)

    for val in json_data:
        if seen[val] == 0:
            adjusted_y.append(val)
        else:
            # Add 0.01 * number of times this value has already appeared
            adjusted_val = val + 0.01 * seen[val]
            adjusted_y.append(adjusted_val)
        seen[val] += 1

    return adjusted_y


def parse_from_idronaut(json_data, depth_array: np.array):
    temp_data = np.array(json_data['x'], dtype='float')

    cleaned_depth = handle_duplicates(json_data['y'])
    depth_data = -1 * np.array(cleaned_depth, dtype='float')
    json_time = np.array([datetime.utcfromtimestamp(json_data['M'][0])])  # Wrap in an array

    # Ensure the temp_data shape matches depth x time
    if temp_data.ndim == 1:  # If temp_data is 1D
        temp_data = temp_data[:, np.newaxis]  # Add a second dimension for 'time'

    # Build the dataset
    raw_meas_data = xr.Dataset(
        {
            'temp': (['depth', 'time'], temp_data)
        },
        coords={
            'time': json_time,
            'depth': depth_data
        }
    )

    interp_meas_data = xr.Dataset(
        {
            'temp': (['depth', 'time'], raw_meas_data['temp'].sel(depth=depth_array, method='nearest').values)
        },
        coords={
            'time': json_time,
            'depth': depth_array
        }
    )

    return interp_meas_data


def parse_from_adcp(json_data: json, depth_array: np.array):
    json_time = np.array(json_data['x'], dtype='datetime64[s]').astype('datetime64[ns]')
    raw_meas_data = xr.Dataset(
        {
            'u': (['depth', 'time'], np.array(json_data['z'], dtype='float')),
            'v': (['depth', 'time'], np.array(json_data['z1'], dtype='float'))
        },
        coords={
            'time': json_time,
            'depth': -1 * np.array(json_data['y'], dtype='float')
        }
    )

    interp_meas_data = xr.Dataset(
        {
            'u': (['depth', 'time'], raw_meas_data['u'].sel(depth=depth_array, method='nearest').values),
            'v': (['depth', 'time'], raw_meas_data['v'].sel(depth=depth_array, method='nearest').values)
        },
        coords={
            'time': json_time,
            'depth': depth_array
        }
    )

    return interp_meas_data


def download_and_parse_from_json_file(file_id: int, dataset_type: str) -> xr.Dataset:
    response = try_download(f'https://api.datalakes-eawag.ch/download/{file_id}')
    json_meas = response.json()

    if dataset_type == 'thermochain':
        meas_data = parse_from_thermochain(json_meas)
    elif dataset_type == 'idronaut':
        depth_array = -0.1 * np.array(range(0, 600))
        meas_data = parse_from_idronaut(json_meas, depth_array)
    elif dataset_type == 'adcp_deep_velocity':
        depth_array = -np.array(range(10, 120))
        meas_data = parse_from_adcp(json_meas, depth_array)
    elif dataset_type == 'adcp_near_surface_velocity':
        depth_array = -np.arange(0, 8, 0.25)  # 0.25
        meas_data = parse_from_adcp(json_meas, depth_array)
    else:
        raise ValueError(f"Couldn't recognise dataset type {dataset_type}.")

    return meas_data


def download_and_parse_from_nc_file(file_id: int, temp_folder: str) -> xr.Dataset:
    response = try_download(f'https://api.datalakes-eawag.ch/download/{file_id}')

    temp_file_path = os.path.join(temp_folder, f"data_{file_id}.nc")
    with open(temp_file_path, "wb") as file:
        file.write(response.content)

    meas_data = xr.open_dataset(temp_file_path, engine="netcdf4")

    return meas_data[['u', 'v']]


def download_data_from_datalakes_dataset(dataset_id: int, start_date: datetime, end_date: datetime,
                                         dataset_type: str = "thermochain", datatype: str = "json",
                                         temp_folder: str = "./temp") :
    response = try_download(f'https://api.datalakes-eawag.ch/files?datasets_id={dataset_id}')
    files_properties = response.json()

    file_ids: list[int] = get_ids_files_filtered_by_datatype(files_properties, datatype)

    if datatype == "json":
        ids_filtered_by_date: list[int] = get_ids_files_filtered_by_dates(files_properties, start_date, end_date)
        file_ids = [file_id for file_id in file_ids if file_id in ids_filtered_by_date]

    datasets = []
    os.makedirs(temp_folder, exist_ok=True)
    depth_profile = None
    for file_id in file_ids:
        if datatype == "json":
            meas_data: xr.Dataset = download_and_parse_from_json_file(file_id, dataset_type)
        elif datatype == "nc":
            meas_data: xr.Dataset = download_and_parse_from_nc_file(file_id, temp_folder)
            depth_array = np.arange(-2.05, 7.8, 0.25)
            meas_data = meas_data.interp(depth=depth_array)
        else:
            raise ValueError(f"Unrecognised datatype {datatype}. Must be either json or nc.")

        datasets.append(meas_data)

    return (datasets, xr.merge(datasets))
