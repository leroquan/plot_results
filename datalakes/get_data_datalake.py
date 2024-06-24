from datetime import datetime
import os
import xarray as xr


def parse_nc_datalakes_from_folder(folder_path: str) -> xr.Dataset:
    nc_files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if file.endswith('.nc')]

    if not nc_files:
        raise FileNotFoundError(f"No NetCDF files found in directory {folder_path}")

    combined_dataset = xr.open_mfdataset(nc_files, combine='by_coords')

    return combined_dataset


def get_timeserie_datalakes(dataset: xr.Dataset, variable: str, given_depth: float) -> xr.DataArray:
    closest_depth = dataset.depth.sel(depth=given_depth, method='nearest')

    return dataset[variable].sel(depth=closest_depth)


def get_profile_datalakes(dataset: xr.Dataset, variable: str, given_time: datetime) -> xr.DataArray:
    closest_time = dataset.time.sel(time=given_time, method='nearest')

    return dataset[variable].sel(time=closest_time)