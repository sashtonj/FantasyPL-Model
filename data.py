import utils
from configparser import ConfigParser


def get_player_summary_url(player_id: int) -> str:
    return f"element-summary/{player_id}/"


def get_my_transfers_url(manager_id: str) -> str:
    return f"entry/{manager_id}/transfers/"


def get_my_team_url(manager_id: str, gameweek: int) -> str:
    return f"entry/{manager_id}/event/{gameweek}/picks/"


def fetch_data(filepath: str, url: str) -> dict:
    """Fetches data from the API or loads it from a JSON file"""
    data = {}
    print(f"Loading data: {url}...")
    # Fetch from API
    data = utils.fetch_data(url)
    utils.write_to_json_file(filepath, data)
    return data


def get_gameweek() -> int:
    events = utils.read_from_json_file('data/basic.json')['events']
    for gw in events:
        if gw['is_current']:
            return int(gw['id'])
    return 0


def main() -> None:
    parser = ConfigParser()
    parser.read('config.ini')

    MANAGER_ID = parser.get('basic', 'id')
    fetch_data(parser.get('data', 'basic'), parser.get('urls', 'bootstrap'))
    fetch_data(parser.get('data', 'fixtures'), parser.get('urls', 'fixtures'))
    fetch_data(parser.get('data', 'my_transfers'), parser.get(
        'urls', 'my_transfers').replace('{{manager_id}}', MANAGER_ID))

    GAMEWEEK = get_gameweek()
    parser.set('basic', 'gw', str(GAMEWEEK))
    with open('config.ini', 'w') as configfile:
        parser.write(configfile)

    my_team_url = parser.get('urls', 'my_team').replace(
        '{{manager_id}}', MANAGER_ID).replace('{{gameweek}}', f"{GAMEWEEK}")
    fetch_data(parser.get('data', 'my_team'), my_team_url)

    player_data = utils.read_from_json_file(parser.get('data', 'basic'))['elements']
    player_data_url = parser.get('data', 'players')
    for player in player_data:
        id = player['id']
        fetch_data(f'{player_data_url}{id}.json', parser.get('urls', 'player').replace('{{player_id}}', f"{id}"))


if __name__ == "__main__":
    main()
