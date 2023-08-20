import utils
from configparser import ConfigParser
from premierleague import PremierLeague, Club, Fixture, Player, Role
from fantasyteam import FantasyTeam


def setup_premier_league(pl: PremierLeague):
    # Populates the premier league instance with all the
    # club and player data
    parser = ConfigParser()
    parser.read('config.ini')

    GAMEWEEK = parser.getint('basic', 'gw')
    BASIC_DATA = utils.read_from_json_file(parser.get('data', 'basic'))
    FIXTURE_DATA = utils.read_from_json_file(parser.get('data', 'fixtures'))

    pl.current_gw = GAMEWEEK

    # Create club instances
    for c in BASIC_DATA['teams']:
        club = Club(c['id'], c['name'], c['short_name'], players={}, fixtures={})
        pl.add_club(club)

    # Attach fixtures to club instances
    for f in FIXTURE_DATA:
        if f['event'] is None:
            continue

        fixture = Fixture(f['id'], f['event'], f['team_h'], f['team_a'], f['team_h_difficulty'], f['team_a_difficulty'])
        pl.clubs[f['team_h']].add_fixture(fixture)
        pl.clubs[f['team_a']].add_fixture(fixture)

    # Create player instances
    for p in BASIC_DATA['elements']:
        player = Player(p['id'], p['first_name'], p['second_name'], p['team'], Role(p['element_type']))
        player.cost = p['now_cost']
        player.form = p['form']
        player.points_per_game = p['points_per_game']
        player.selected_by_percent = p['selected_by_percent']
        player.total_points = p['total_points']
        player.chance_of_playing = p['chance_of_playing_next_round']

        for f in utils.read_from_json_file(f"{parser.get('data', 'players')}{p['id']}.json")['history']:
            player.add_gameweek_stat(f['round'], 'points', f['total_points'])
            player.add_gameweek_stat(f['round'], 'minutes', f['minutes'])

        pl.get_club(p['team']).add_player(player)

    return pl


def setup_fantasy_team(pl: PremierLeague) -> FantasyTeam:
    parser = ConfigParser()
    parser.read('config.ini')

    TEAM_DATA = utils.read_from_json_file(parser.get('data', 'my_team'))
    TRANSFER_DATA = utils.read_from_json_file(parser.get('data', 'my_transfers'))

    team = FantasyTeam(pl.current_gw)

    players = pl.get_players()
    team.bank = TEAM_DATA['entry_history']['bank']
    team.squad_value = TEAM_DATA['entry_history']['value']

    # wildcards = int(parser.get('basic', 'wildcards'))
    # if TEAM_DATA['active_chip'] == "wildcard":
    #     wildcards += 1
    #     parser.set('basic', 'wildcards', f"{wildcards}")

    # team.wildcards = wildcards

    with open('config.ini', 'w') as configfile:
        parser.write(configfile)

    for p in TEAM_DATA['picks']:
        player = players.get(p['element'])
        if player is None:
            continue

        team.players[player.id] = player
        if p['position'] < 12:
            # < 12 indicates played was in the starting eleven
            team.starting.append(player.id)
        else:
            team.bench.append(player.id)

        if p['is_captain']:
            team.captain = player.id
        elif p['is_vice_captain']:
            team.vice_captain = player.id

    for t in TRANSFER_DATA:
        # We use t['event'] to only save transfers from the current gameweek
        if t['event'] == pl.current_gw:
            players_in = players[t['element_in']]
            players_out = players[t['element_out']]
            team.transfers_in.append(players_in)
            team.transfers_out.append(players_out)

    return team
