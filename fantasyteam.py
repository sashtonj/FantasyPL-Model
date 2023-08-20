from dataclasses import dataclass, field
from typing import List, Dict
from premierleague import Player


@dataclass
class FantasyTeam:
    gameweek: int
    players: Dict[int, Player] = field(default_factory=dict)
    starting: List[int] = field(default_factory=list)
    bench: List[int] = field(default_factory=list)
    captain: int = 0
    vice_captain: int = 0
    transfers_in: List[Player] = field(default_factory=list)
    transfers_out: List[Player] = field(default_factory=list)
    bank: int = 0
    squad_value: int = 0

    def get_players(self) -> List[Player]:
        return list(self.players.values())

    def get_squad_value(self) -> int:
        return sum([p.cost for p in self.players.values()])

    def display_starting(self) -> None:
        print("\nStarting 11:")
        self.starting.sort(key=lambda x: self.players[x].role)
        for p in self.starting:
            player = self.players[p]
            captain = ' (C)' if self.captain == player else ''
            vice = ' (VC)' if self.vice_captain == player else ''
            print(f"({player.role.name}) {player.name}{captain}{vice}")

    def display_bench(self) -> None:
        print("\nBench:")
        self.bench.sort(key=lambda x: self.players[x].role)
        for p in self.bench:
            player = self.players[p]
            print(f"({player.role.name}) {player.name}")

    def display_transfers_in(self) -> None:
        print("\nTransfers In:")
        for p in self.transfers_in:
            print(p.name, p.cost)

    def display_transfers_out(self) -> None:
        print("\nTransfers Out:")
        for p in self.transfers_out:
            print(p.name, p.cost)

    def display_transfers(self) -> None:
        self.display_transfers_in()
        self.display_transfers_out()

    def display_squad(self) -> None:
        self.display_starting()
        self.display_bench()

    def display_financials(self) -> None:
        print(f"Bank Balance: {self.bank}\nSquad Value: {self.get_squad_value()}")

    def display_gameweek(self) -> None:
        self.display_financials()
        self.display_transfers()
        self.display_squad()
