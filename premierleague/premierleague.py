from .club import Club
from .player import Player
from .role import Role


class PremierLeague:

    def __init__(self) -> None:
        self.clubs = {}
        self.current_gw = 0

    def add_club(self, club: Club) -> None:
        self.clubs[club.id] = club

    def get_club(self, club_id) -> Club:
        return self.clubs[club_id]

    def get_players(self) -> dict:
        players = {}
        for club in self.clubs.values():
            players = players | club.players
        return players

    def get_players_by_role(self, role: Role) -> dict:
        players = {}
        for club in self.clubs.values():
            players = players | club.get_players_by_role(role)
        return players

    def get_player_by_id(self, id: int) -> Player:
        return self.get_players()[id]
