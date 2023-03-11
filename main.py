import utils
from premierleague import Player, Club, Fixture, PremierLeague, Role
from fantasyteam import FantasyTeam
from model import FantasyModel


MANAGER_ID = "6082478"
BASE_URL = "https://fantasy.premierleague.com/api/"
BASIC_DATA_URL = "bootstrap-static/"
FIXTURES_URL = "fixtures/"

REFRESH = False
HORIZON_LENGTH = 3
PAST_GAMEWEEKS = 3


def get_player_summary_url(player_id: int) -> str:
    return f"element-summary/{player_id}/"


def get_my_transfers_url(manager_id: str) -> str:
    return f"entry/{manager_id}/transfers/"


def get_my_team_url(manager_id: str, gameweek: int) -> str:
    return f"entry/{manager_id}/event/{gameweek}/picks/"


def load_data(filepath: str, url: str, refresh: bool = False) -> dict:
    """Fetches data from the API or loads it from a JSON file"""
    data = {}
    print(f"Loading data: {url}...")
    if refresh:
        # Fetch from API
        data = utils.fetch_data(url)
        utils.write_to_json_file(filepath, data)
        return data

    # Read from JSON file
    return utils.read_from_json_file(filepath)

# --------------------
# Load Data
# --------------------


basic_data = load_data('data/basic.json', BASE_URL + BASIC_DATA_URL, refresh=REFRESH)
fixture_data = load_data('data/fixtures.json', BASE_URL + FIXTURES_URL, refresh=REFRESH)
transfer_data = load_data('data/my_transfers.json', BASE_URL + get_my_transfers_url(MANAGER_ID), refresh=REFRESH)

player_data = {}
for player in basic_data['elements']:
    id = player['id']
    player_data[id] = load_data(f'data/players/{id}.json', BASE_URL + get_player_summary_url(id), refresh=REFRESH)

# Set the current gameweek
current_gw = 0
for gw in basic_data['events']:
    if gw['is_current']:
        current_gw = gw['id']

my_team_data = load_data('data/my_team.json', BASE_URL + get_my_team_url(MANAGER_ID, current_gw), refresh=REFRESH)

# --------------------
# Establish club, player, and league instances
# --------------------

pl = PremierLeague()
pl.current_gw = current_gw

# Create club instances
for c in basic_data['teams']:
    club = Club(c['id'], c['name'], c['short_name'], players={}, fixtures={})
    pl.add_club(club)

for f in fixture_data:
    if f['event'] is None:
        continue

    fixture = Fixture(f['id'], f['event'], f['team_h'], f['team_a'], f['team_h_difficulty'], f['team_a_difficulty'])
    pl.clubs[f['team_h']].add_fixture(fixture)
    pl.clubs[f['team_a']].add_fixture(fixture)

# Create player instances
for p in basic_data['elements']:
    player = Player(p['id'], p['first_name'], p['second_name'], p['team'], Role(p['element_type']))
    player.cost = p['now_cost']
    player.form = p['form']
    player.points_per_game = p['points_per_game']
    player.selected_by_percent = p['selected_by_percent']
    player.total_points = p['total_points']
    player.chance_of_playing = p['chance_of_playing_next_round']

    for f in player_data[p['id']]['history']:
        player.add_gameweek_stat(f['round'], 'points', f['total_points'])
        player.add_gameweek_stat(f['round'], 'minutes', f['minutes'])

    pl.get_club(p['team']).add_player(player)

team = FantasyTeam()
players = pl.get_players()
team.bank = my_team_data['entry_history']['bank']
team.squad_value = my_team_data['entry_history']['value']
for p in my_team_data['picks']:
    team.players.setdefault(pl.current_gw, {})[p['element']] = players.get(p['element'])

    if p['position'] < 12:
        team.starting.setdefault(pl.current_gw, []).append(p['element'])
    else:
        team.bench.setdefault(pl.current_gw, []).append(p['element'])

    if p['is_captain']:
        team.captain[pl.current_gw] = players[p['element']]
    elif p['is_vice_captain']:
        team.vice_captain[pl.current_gw] = players[p['element']]


model = FantasyModel(pl, team)
model.solve(HORIZON_LENGTH, PAST_GAMEWEEKS)

for gw in range(pl.current_gw, pl.current_gw + model.horizon_len):
    print(f"\n------------\nGameweek: {gw}\n------------")
    team.display_gameweek(gw)
