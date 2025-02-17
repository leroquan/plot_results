import numpy as np


def translate_grid_to_origin(x: np.ndarray, y: np.ndarray, dx: float, dy: float) -> (np.ndarray, np.ndarray):
    trans_x = x + dx
    trans_y = y + dy

    return trans_x, trans_y


def get_grid_angle(x0: float, y0: float, x1: float, y1: float) -> float:
    grid_angle = np.arctan2(y1 - y0, x1 - x0)

    return grid_angle


def rotate_grid(x: np.ndarray, y: np.ndarray, x0: float, y0: float, rotation_angle: float) -> (np.ndarray, np.ndarray):
    x_translated_to_zero, y_translated_to_zero = translate_grid_to_origin(x, y, -x0, -y0)

    x_rotated = np.cos(rotation_angle) * x_translated_to_zero - np.sin(rotation_angle) * y_translated_to_zero
    y_rotated = np.sin(rotation_angle) * x_translated_to_zero + np.cos(rotation_angle) * y_translated_to_zero

    x_translated_back, y_translated_back = translate_grid_to_origin(x_rotated, y_rotated, x0, y0)

    return x_translated_back, y_translated_back

