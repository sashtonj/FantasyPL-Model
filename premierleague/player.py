from dataclasses import dataclass, field
from .role import Role


@dataclass
class Player:
    id: int
    first_name: str
    surname: str
    club_id: int
    role: Role
    cost: int = 0
    gameweek_stats: dict = field(default_factory=dict)
    form: float = 0.0
    points_per_game: float = 0.0
    selected_by_percent: float = 0.0
    points: dict = field(default_factory=dict)
    minutes: dict = field(default_factory=dict)
    total_points: int = 0
    _chance_of_playing: float = 0.0

    @property
    def chance_of_playing(self) -> float:
        return self._chance_of_playing

    @chance_of_playing.setter
    def chance_of_playing(self, value: int | None) -> None:
        if value is None:
            value = 100
        self._chance_of_playing = round(value / 100, 1)

    @property
    def name(self):
        return f"{self.first_name} {self.surname}"

    def add_points(self, points: int, gw: int) -> None:
        self.points.setdefault(gw, []).append(points)

    def add_gameweek_stat(self, gw: int, stat: str, value: int | float | None) -> None:
        getattr(self, stat).setdefault(gw, []).append(value)
