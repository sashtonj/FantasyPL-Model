from dataclasses import dataclass, field


@dataclass
class FantasyTeam:
    players: dict = field(default_factory=dict)
    starting: dict = field(default_factory=dict)
    bench: dict = field(default_factory=dict)
    captain: dict = field(default_factory=dict)
    vice_captain: dict = field(default_factory=dict)
    transfers_in: dict = field(default_factory=dict)
    transfers_out: dict = field(default_factory=dict)
    bank: int = 0
    squad_value: int = 0

    def display_starting(self, gw: int) -> None:
        print("\nStarting 11:")
        for p in self.starting.get(gw, []):
            player = self.players[gw].get(p)
            captain = '(C)' if self.captain[gw] == player else ''
            vice = '(VC)' if self.vice_captain[gw] == player else ''
            print(f"({player.role.name}) {player.name} {captain} {vice} ({(player.club_id)})")

    def display_bench(self, gw: int) -> None:
        print("\nBench:")
        for p in self.bench.get(gw, []):
            player = self.players[gw].get(p)
            print(f"({player.role.name}) {player.name} ({player.club_id})")

    def display_transfers_in(self, gw: int) -> None:
        print("\nTransfers In:")
        for p in self.transfers_in.get(gw, []):
            print(p.name)

    def display_transfers_out(self, gw: int) -> None:
        print("\nTransfers Out:")
        for p in self.transfers_out.get(gw, []):
            print(p.name)

    def display_transfers(self, gw: int) -> None:
        self.display_transfers_in(gw)
        self.display_transfers_out(gw)

    def display_squad(self, gw: int) -> None:
        self.display_starting(gw)
        self.display_bench(gw)

    def display_gameweek(self, gw: int) -> None:
        self.display_transfers(gw)
        self.display_squad(gw)
