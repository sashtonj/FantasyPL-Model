class FantasyTeam:

    def __init__(self) -> None:
        self.players = {}
        self.starting = {}
        self.bench = {}
        self.bank = 0
        self.squad_value = 0
        self.captain = {}
        self.vice_captain = {}
        self.transfers_in = {}
        self.transfers_out = {}

    def display_squad(self, gw: int) -> None:
        print("\nStarting 11:")
        for p in self.starting.get(gw, []):
            player = self.players[gw].get(p)
            captain = '(C)' if self.captain[gw] == player else ''
            vice = '(VC)' if self.vice_captain[gw] == player else ''
            print(f"({player.role.name}) {player.name} {captain} {vice} ({(player.club_id)})")

        print("\nBench:")
        for p in self.bench.get(gw, []):
            player = self.players[gw].get(p)
            print(f"({player.role.name}) {player.name} ({player.club_id})")

    def display_transfers(self, gw: int) -> None:
        print("\nTransfers Out:")
        for p in self.transfers_out.get(gw, []):
            print(p.name)

        print("\nTransfers In:")
        for p in self.transfers_in.get(gw, []):
            print(p.name)
