import requests
import json
from clubs import Club
from premier_league import PremierLeague, Squad


def get_API_data(url):
    response_data = requests.get(url)
    return json.loads(response_data.text)


def setup_clubs(club_data):
    clubs = {}
    for c in club_data:
        # Create club instances
        clubs[c['id']] = Club(c)
    return clubs


def setup_players(clubs, player_data):
    counter = 0
    for p in player_data:
        p['id'] = counter
        clubs[p['team']].add_player(p)
        counter += 1


def setup_fixtures(clubs, data):
    for f in data:
        clubs[f['team_h']].add_fixture({'gw': f['event'], 'opponent': f['team_a'],
                                       'difficulty': f['team_h_difficulty']})
        clubs[f['team_a']].add_fixture({'gw': f['event'], 'opponent': f['team_h'],
                                        'difficulty': f['team_a_difficulty']})


def setup(api_url, fixture_url):
    data = get_API_data(api_url)
    clubs = setup_clubs(data['teams'])
    setup_players(clubs, data['elements'])
    setup_fixtures(clubs, get_API_data(fixture_url))

    return PremierLeague(clubs), Squad()
