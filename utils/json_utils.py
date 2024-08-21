import json
import os
from utils import try_download


def download_json(url: str):
    response = try_download(url)
    json_data = response.json()

    return json_data


def open_json(file_path: str) -> json:
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json(json_data: json, save_path) -> None:
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, 'w') as f:
        json.dump(json_data, f, indent=4)
