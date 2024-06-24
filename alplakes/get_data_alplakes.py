import json
import os
import pandas as pd
import requests


def try_download(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(r"Didn't work, response.status_code = " + str(response.status_code) + ", url = " + url)

    return response


def download_3d_timeserie_from_api(lake_name: str, start_date: str, end_date: str, depth: float, lat_wgs84: float,
                                   lon_wgs84: float, save_file_path: str) -> None:
    url = f"https://alplakes-api.eawag.ch/simulations/point/delft3d-flow/{lake_name}/{start_date}/{end_date}/{depth}/{lat_wgs84}/{lon_wgs84}"
    response = try_download(url)

    alplakes_timeserie_data = response.json()
    os.makedirs(os.path.dirname(save_file_path), exist_ok=True)
    with open(save_file_path, 'w') as f:
        json.dump(alplakes_timeserie_data, f, indent=4)


def parse_json_3d_timeserie_to_df(json_file: str) -> pd.DataFrame:
    with open(json_file) as f:
        data = json.load(f)
    refactored_data = {
        'time': data['time'],
        'temperature': data['temperature']['data']
    }
    df_data = pd.DataFrame(refactored_data)
    df_data['time'] = pd.to_datetime(df_data['time'])

    return df_data


def parse_alplakes_3d_timeserie_from_directory(json_directory_path: str) -> pd.DataFrame:
    json_files = [os.path.join(json_directory_path, file)
                  for file in os.listdir(json_directory_path)
                  if file.endswith('.json')]

    if not json_files:
        raise FileNotFoundError(f"No json files found in directory {json_directory_path}")

    dataframes = [parse_json_3d_timeserie_to_df(json_file) for json_file in json_files]

    return pd.concat(dataframes)


def download_3d_profile_from_api(lake_name: str, date_plot_profil: str, lat_wgs84: float,
                                 lon_wgs84: float, save_file_path: str) -> None:
    url = f"https://alplakes-api.eawag.ch/simulations/profile/delft3d-flow/{lake_name}/{date_plot_profil}/{lat_wgs84}/{lon_wgs84}"
    response = try_download(url)
    alplakes_profile_data = response.json()
    os.makedirs(os.path.dirname(save_file_path), exist_ok=True)
    with open(save_file_path, 'w') as f:
        json.dump(alplakes_profile_data, f, indent=4)


def parse_json_3d_profile_to_df(json_file: str) -> pd.DataFrame:
    with open(json_file) as f:
        data = json.load(f)
    refactored_data = {
        'depth': data['depth']['data'],
        'temperature': data['temperature']['data']
    }

    return pd.DataFrame(refactored_data)


def parse_json_1d_timeserie_to_df(json_file: str) -> pd.DataFrame:
    with open(json_file) as f:
        data = json.load(f)
    refactored_data = {
        'time': data['time'],
        'temperature': data['temperature']['data']
    }
    df_data = pd.DataFrame(refactored_data)
    df_data['time'] = pd.to_datetime(df_data['time'])

    return df_data