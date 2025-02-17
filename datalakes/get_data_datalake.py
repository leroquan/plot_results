from datetime import datetime
import os

import xarray as xr
import numpy as np
import json

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


def download_ids_files_filtered_by_dates(dataset_id: int, start_date: datetime, end_date: datetime) -> list[int]:
    response = try_download(f'https://api.datalakes-eawag.ch/files?datasets_id={dataset_id}')
    files_properties = response.json()

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


def parse_from_idronaut(json_data, depth_array: np.array):
    temp_data = np.array(json_data['x'], dtype='float')
    depth_data = -1 * np.array(json_data['y'], dtype='float')
    time_data = np.array([datetime.utcfromtimestamp(json_data['M'][0])])  # Wrap in an array

    # Ensure the temp_data shape matches depth x time
    if temp_data.ndim == 1:  # If temp_data is 1D
        temp_data = temp_data[:, np.newaxis]  # Add a second dimension for 'time'

    # Build the dataset
    raw_meas_data = xr.Dataset(
        {
            'temp': (['depth', 'time'], temp_data)
        },
        coords={
            'time': time_data,
            'depth': depth_data
        }
    )

    interp_meas_data = xr.Dataset(
        {
            'temp': (['depth', 'time'], raw_meas_data['temp'].sel(depth=depth_array, method='nearest').values)
        },
        coords={
            'time': time_data,
            'depth': depth_array
        }
    )

    return interp_meas_data


def download_data_from_datalakes_file(file_id: int, dataset_type: str) -> xr.Dataset:
    response = try_download(f'https://api.datalakes-eawag.ch/download/{file_id}')
    json_meas = response.json()

    if dataset_type == 'thermochain':
        meas_data = parse_from_thermochain(json_meas)
    elif dataset_type == 'idronaut':
        depth_array = -0.1 * np.array(range(0, 600))
        meas_data = parse_from_idronaut(json_meas, depth_array)
    else:
        raise ValueError(f"Couldn't recognise dataset type {dataset_type}.")

    return meas_data


def download_data_from_datalakes_dataset(dataset_id: int, start_date: datetime, end_date: datetime,
                                         dataset_type: str = "thermochain") -> xr.Dataset:
    file_ids: list[int] = download_ids_files_filtered_by_dates(dataset_id, start_date, end_date)
    merged_ds = None
    for file_id in file_ids:
        meas_data: xr.Dataset = download_data_from_datalakes_file(file_id, dataset_type)
        if merged_ds is None:
            merged_ds = meas_data
        else:
            merged_ds = xr.merge([merged_ds, meas_data])
    return merged_ds
