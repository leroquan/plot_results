import numpy as np
import pandas as pd
import xarray as xr
from datetime import datetime


def interpolate_to_axis(xr_ds: xr.DataArray, axis, axis_name: str, max_gap=None) -> xr.DataArray:
    """Interpolate a xarray DataArray on a given axis. Axis type depends on what is interpolated
    (f.ex. an array of DateTime for time axis, or an array of numbers for depth axis).
    If max_gap is provided, the interpolation is not performed on points for which data is not available
    less than max_gap away from the point."""

    interp_ds = xr_ds.interp({axis_name: axis})

    if max_gap is not None:
        nearest_values = xr_ds[axis_name].sel({axis_name: axis}, method="nearest")
        diff = abs(nearest_values - axis)
        invalid_axis = axis[np.array(diff <= max_gap)]
        mask = interp_ds[axis_name].isin(invalid_axis)
        interp_ds = interp_ds.where(mask, np.nan)

    return interp_ds


def resample_time(xr_ds: xr.DataArray, start_date: datetime, end_date: datetime, time_step: np.timedelta64,
                  max_time_gap_allowed: np.timedelta64 = None, axis_name: str = 'time') -> xr.DataArray:
    time_axis = pd.date_range(
        start=pd.Timestamp(start_date).normalize(),
        end=pd.Timestamp(end_date),
        freq=time_step
    )

    return interpolate_to_axis(xr_ds, time_axis, axis_name, max_time_gap_allowed)


def resample_depth(xr_ds: xr.DataArray, min_depth: float, max_depth: float, step: float,
                   max_gap_allowed: float = None, axis_name: str = 'depth') -> xr.DataArray:
    depth_axis = np.arange(min_depth, max_depth, step)

    return interpolate_to_axis(xr_ds, depth_axis, axis_name, max_gap_allowed)
