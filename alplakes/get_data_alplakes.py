import json
import os
import glob
import pandas as pd
import numpy as np
from datetime import datetime
import xarray as xr

from utils import (download_json,
                   open_json)


def download_3d_timeserie_from_api(lake_name: str, start_date: str, end_date: str, depth: float, lat_wgs84: float,
                                   lon_wgs84: float) -> json:
    url = (f"https://alplakes-api.eawag.ch/simulations/point/delft3d-flow/"
           f"{lake_name}/"
           f"{start_date}/"
           f"{end_date}/"
           f"{depth}/"
           f"{lat_wgs84}/"
           f"{lon_wgs84}"
           )
    alplakes_timeserie_data = download_json(url)

    return alplakes_timeserie_data


def parse_alplakes_json_3d_timeserie_to_df(json_data: json) -> pd.DataFrame:
    refactored_data = {
        'time': json_data['time'],
        'temperature': json_data['variables']['T']['data']
    }
    df_data = pd.DataFrame(refactored_data)
    df_data['time'] = pd.to_datetime(df_data['time'])

    return df_data


def parse_alplakes_3d_timeserie_from_directory(json_directory_path: str) -> pd.DataFrame:
    json_files_paths = glob.glob(os.path.join(json_directory_path, '*.json'))
    if not json_files_paths:
        raise FileNotFoundError(f"No json files found in directory {json_directory_path}")
    dataframes = [
        parse_alplakes_json_3d_timeserie_to_df(open_json(json_path))
        for json_path
        in json_files_paths
    ]

    return pd.concat(dataframes)


def get_3d_profile_from_api(lake_name: str, date_plot_profile: str, lat_wgs84: float, lon_wgs84: float) -> json:
    url = (f"https://alplakes-api.eawag.ch/simulations/profile/delft3d-flow/"
           f"{lake_name}/"
           f"{date_plot_profile}/"
           f"{lat_wgs84}/"
           f"{lon_wgs84}")
    alplakes_profile_data = download_json(url)

    return alplakes_profile_data


def parse_json_3d_profile_to_df(json_file: json) -> pd.DataFrame:
    refactored_data = {
        'depth': json_file['depth']['data'],
        'temperature': json_file['variables']['temperature']['data']
    }

    return pd.DataFrame(refactored_data)


def parse_json_1d_timeserie_to_df(json_file: str) -> pd.DataFrame:
    with open(json_file) as f:
        data = json.load(f)
    refactored_data = {
        'time': data['time'],
        'temperature': data['variables']['temperature']['data']
    }
    df_data = pd.DataFrame(refactored_data)
    df_data['time'] = pd.to_datetime(df_data['time'])

    return df_data


def parse_alplakes_1d_from_directory(folder_path: str) -> xr.Dataset:
    json_files = glob.glob(os.path.join(folder_path, f'*.json'))

    # Initialize lists to store combined data
    all_times = []
    all_depths = []
    all_temperatures = []

    # Loop through each JSON file
    for file_path in json_files:
        # Read the JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Extract time data and convert to datetime
        times = [datetime.fromisoformat(t.replace('Z', '+00:00')) for t in data['time']]

        # Extract depth and temperature data
        depths = np.array(data['depth']['data'])
        temperatures = np.array(data['variables']['T']['data'])

        # Append to the combined lists
        all_times.append(times)
        all_depths.append(depths)
        all_temperatures.append(temperatures)

    # Ensure all depth arrays are consistent
    if len(set(len(d) for d in all_depths)) != 1:
        raise ValueError("Depth arrays are not consistent across files.")

    # Use the first depth array (assumed consistent across files)
    depths = all_depths[0]

    # Combine all time and temperature data
    all_times = np.concatenate(all_times)
    all_times = np.array([dt.replace(tzinfo=None) for dt in all_times])
    all_temperatures = np.hstack(all_temperatures)

    # Create xarray dataset
    simstrat_data = xr.Dataset(
        {
            'temperature': (['depth', 'time'], np.stack(all_temperatures))
        },
        coords={
            'time': all_times,
            'depth': depths
        }
    )

    return simstrat_data
