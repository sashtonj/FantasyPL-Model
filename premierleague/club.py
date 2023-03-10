from dataclasses import dataclass
from .player import Player
from .role import Role


@dataclass
class Fixture:
    id: int
    gameweek: int
    home_team: int
    away_team: int
    home_team_difficulty: int
    away_team_difficulty: int


@dataclass
class Club:
    id: int
    name: str
    short_name: str
    players: dict
    fixtures: dict

    def get_players_by_role(self, role: Role) -> dict:
        return {id: p for id, p in self.players.items() if p.role == role}

    def get_goalkeepers(self) -> dict:
        return self.get_players_by_role(Role.GK)

    def get_defenders(self) -> dict:
        return self.get_players_by_role(Role.DF)

    def get_midfielders(self) -> dict:
        return self.get_players_by_role(Role.MF)

    def get_forwards(self) -> dict:
        return self.get_players_by_role(Role.FW)

    def add_player(self, player: Player) -> None:
        self.players[player.id] = player

    def add_fixture(self, fixture: Fixture) -> None:
        self.fixtures.setdefault(fixture.gameweek, []).append(fixture)
