from dataclasses import dataclass
from .role import Role


@dataclass
class Player:
    id: int
    first_name: str
    surname: str
    club_id: int
    role: Role
    cost: int
    gameweek_stats: dict
    form: float = 0.0
    points_per_game: float = 0.0
    selected_by_percent: float = 0.0
    total_points: int = 0
    chance_of_playing: float = 0.0

    def __post_init__(self):
        ...

    @property
    def name(self):
        return f"{self.first_name} {self.surname}"

    def add_gameweek_stats(self, gw: int, fixture: int, points: int, minutes: int) -> None:
        self.gameweek_stats.setdefault(gw, []).append({
            "fixture": fixture,
            "points": points,
            "minutes": minutes
        })
