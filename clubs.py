from player import Player


class Club:

    def __init__(self, club):
        self.club = club
        self.players = []
        self.fixtures = {}

    def add_player(self, player):
        self.players.append(Player(player))

    def add_fixture(self, fixture):
        if self.fixtures.get(fixture['gw']):
            self.fixtures[fixture['gw']].append(fixture)
            return
        self.fixtures[fixture['gw']] = [fixture]

    def get_fixtures(self, gameweek):
        return self.fixtures[gameweek]

    def get_players(self):
        return self.players

    def get_players_of_position(self, pos):
        return [p for p in self.players if p.get_position() == pos]

    def get_goalkeepers(self):
        return self.get_players_of_position(1)

    def get_defenders(self):
        return self.get_players_of_position(2)

    def get_midfielders(self):
        return self.get_players_of_position(3)

    def get_forwards(self):
        return self.get_players_of_position(4)

    def get_next_fixture_difficulty(self):
        return self.fixtures[0]['difficulty']
