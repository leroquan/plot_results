import numpy as np


def compute_rmse(prediction: np.array, measures: np.array) -> float:
    return np.sqrt(np.nanmean((prediction - measures) ** 2))
