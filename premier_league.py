class Squad:
    def __init__(self):
        self.squad = {}
        self.transfers = {}

    def add_to_squad(self, gameweek, value, key):
        self.squad.setdefault(gameweek, {}).setdefault(key, []).append(value)

    def set_captain(self, player, gameweek):
        self.add_to_squad(gameweek, player, 'captain')

    def set_vice_captain(self, player, gameweek):
        self.add_to_squad(gameweek, player, 'vice_captain')

    def add_goalkeeper(self, player, gameweek):
        self.add_to_squad(gameweek, player, 'goalkeepers')

    def add_defender(self, player, gameweek):
        self.add_to_squad(gameweek, player, 'defenders')

    def add_midfielder(self, player, gameweek):
        self.add_to_squad(gameweek, player, 'midfielders')

    def add_forward(self, player, gameweek):
        self.add_to_squad(gameweek, player, 'forwards')

    def add_to_bench(self, player, gameweek):
        self.add_to_squad(gameweek, player, 'bench')

    def add_player(self, player, gameweek):
        pos = player.get_position()
        if pos == 1:
            self.add_goalkeeper(player, gameweek)
        elif pos == 2:
            self.add_defender(player, gameweek)
        elif pos == 3:
            self.add_midfielder(player, gameweek)
        elif pos == 4:
            self.add_forward(player, gameweek)

    def set_chip(self, chip, value, gameweek):
        self.add_to_squad(gameweek, value, chip)

    def transfer_in(self, player, gameweek):
        self.transfers.setdefault(gameweek, {}).setdefault('in', []).append(player)

    def transfer_out(self, player, gameweek):
        self.transfers.setdefault(gameweek, {}).setdefault('out', []).append(player)

    def display(self):
        for g in self.squad.keys():
            print(f"\nGameweek {g}:\n-----")

            print("\nTransfer In:")
            for player in self.transfers.get(g, {}).get('in', []):
                print(f"{player.get_name()}")

            print("\nTransfer Out:")
            for player in self.transfers.get(g, {}).get('out', []):
                print(f"{player.get_name()}")

            pos = ['goalkeepers', 'defenders', 'midfielders', 'forwards', 'bench', 'captain', 'vice_captain']
            for p in pos:
                print(f"\n{(p.upper())}:")
                for player in self.squad[g][p]:
                    print(f"{player.get_name()}")


class PremierLeague:

    clubs = {}
    gameweeks = range(17, 20)  # usually range(17, 39)

    def __init__(self, clubs):
        self.clubs = clubs

    def get_club(self, id):
        return self.clubs[id]

    def get_clubs(self):
        return self.clubs

    def get_players(self):
        return [player for c in self.clubs.values() for player in c.get_players()]

    def get_goalkeepers(self):
        return [player for c in self.clubs.values() for player in c.get_goalkeepers()]

    def get_defenders(self):
        return [player for c in self.clubs.values() for player in c.get_defenders()]

    def get_midfielders(self):
        return [player for c in self.clubs.values() for player in c.get_midfielders()]

    def get_forwards(self):
        return [player for c in self.clubs.values() for player in c.get_forwards()]
