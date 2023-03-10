import requests
import json


def fetch_data(url):
    try:
        response_data = requests.get(url)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    return json.loads(response_data.text)


def parse_numeric_keys(x):
    if isinstance(x, dict):
        return {int(k) if k.isnumeric() else k: x[k] for k in x.keys()}


def write_to_json_file(filepath: str, data: object) -> None:
    with open(filepath, "w+") as file:
        json.dump(data, file)


def read_from_json_file(filepath: str) -> dict:
    with open(filepath, "r") as file:
        return json.load(file, object_hook=parse_numeric_keys)
