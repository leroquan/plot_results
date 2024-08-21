import requests


def try_download(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(r"Didn't work, response.status_code = " + str(response.status_code) + ", url = " + url)

    return response
