import sys
from pulp import LpVariable, LpProblem, LpStatus, LpMaximize, LpBinary, LpInteger, lpSum, value as lpValue
from premierleague import PremierLeague
from premierleague.role import Role
from fantasyteam import FantasyTeam


class Model:

    def __init__(self, pl: PremierLeague, team: FantasyTeam) -> None:
        self.pl = pl
        self.team = team
        self.model = LpProblem(name='fantasypl', sense=LpMaximize)
        self.gameweek = self.pl.current_gw

    def solve(self, horizon: int = 10) -> dict[int, FantasyTeam]:
        # ----------------------------------------
        # Sets & Subsets
        # ---------------------------------------
        # Set of players
        P = self.pl.get_players().values()

        # Set of clubs
        C = self.pl.clubs.values()

        # Set of gameweeks
        G = range(self.gameweek, self.gameweek + horizon + 1)

        # Set of roles (player positions)
        R = list(Role)

        P_r = {
            Role.GK: self.pl.get_players_by_role(Role.GK).values(),
            Role.DF: self.pl.get_players_by_role(Role.DF).values(),
            Role.MF: self.pl.get_players_by_role(Role.MF).values(),
            Role.FW: self.pl.get_players_by_role(Role.FW).values()
        }

        # ----------------------------------------
        # Parameters
        # ---------------------------------------
        # Number of players of role r required to make up a squad of 15
        n_r = {Role.GK: 2, Role.DF: 5, Role.MF: 5, Role.FW: 3}

        # Lower bound on the number of players of role r that must be in the starting 11
        l_r = {Role.GK: 1, Role.DF: 3, Role.MF: 3, Role.FW: 1}

        # Upper bound on the number of players of role r that must be in the starting 11
        u_r = {Role.GK: 1, Role.DF: 5, Role.MF: 5, Role.FW: 3}

        # Balance remaining
        b_r = 1000

        # Did we make a transfer this week
        t = 0
        if self.gameweek < 2:
            t = 1
        elif len(self.team.transfers_in) > 0:
            t = 1

        # ----------------------------------------
        # Decision Variables
        # ---------------------------------------

        # Player p is in the starting 11 in gameweek g
        x = LpVariable.dicts("Starting", ((p.id, g) for p in P for g in G), cat=LpBinary)

        # player p is on the bench in gameweek g
        y = LpVariable.dicts("Benched", ((p.id, g) for p in P for g in G), cat=LpBinary)

        # Player p has been selected in gameweek g (Derived from x and y)
        z = LpVariable.dicts("Selected", ((p.id, g) for p in P for g in G), cat=LpBinary)

        # Player p is club captain during gameweek g
        cc = LpVariable.dicts("Captain", ((p.id, g) for p in P for g in G), cat=LpBinary)

        # Player p is vice captain during gameweek g
        vc = LpVariable.dicts("Vice_captain", ((p.id, g) for p in P for g in G), cat=LpBinary)

        # Player p has been transferred in during gameweek g
        t_in = LpVariable.dicts("Transferred_in", ((p.id, g) for p in P for g in G), cat=LpBinary)

        # Player p has been transferred in during gameweek g
        t_out = LpVariable.dicts("Transferred_out", ((p.id, g) for p in P for g in G), cat=LpBinary)

        b = LpVariable.dicts("Bank", (g for g in G), cat=LpInteger)

        # wc = LpVariable.dicts("Wildcard", (g for g in G), cat=LpInteger)

        for g in G:

            if g == self.gameweek:
                # Set initial squad
                for p in self.team.starting:
                    x[(p, g)].setInitialValue(1)
                    x[(p, g)].fixValue()

                for p in self.team.bench:
                    y[(p, g)].setInitialValue(1)
                    y[(p, g)].fixValue()

                # Set current Captain
                cc[(self.team.captain, g)].setInitialValue(1)
                cc[(self.team.captain, g)].fixValue()

                # Set current vice Captain
                vc[(self.team.vice_captain, g)].setInitialValue(1)
                vc[(self.team.vice_captain, g)].fixValue()

                # Set current bank
                b[g].setInitialValue(self.team.bank)
                b[g].fixValue()

            # Starting 11 must have 11 players
            name = f"GW {g}: Starting 11 must have 11 players..."
            self.model += lpSum([x[(p.id, g)] for p in P]) == 11, name

            name = f"GW {g}: Must have a captain selected"
            self.model += lpSum([cc[(p.id, g)] for p in P]) == 1, name

            name = f"GW {g}: Must have a vice captain selected"
            self.model += lpSum([vc[(p.id, g)] for p in P]) == 1, name

            if g > self.gameweek:
                name = f"GW {g}: Maximum of 2 free transfers in to the team during each gameweek"
                self.model += lpSum([t_in[(p.id, g)] for p in P]) <= 2 - t + (wc[g] * 13) + (wc[g] * t), name

                name = f"GW {g}: Maximum of 2 free transfers out of the team during each gameweek"
                self.model += lpSum([t_out[(p.id, g)] for p in P]) <= 2 - t, name

                name = f"GW {g}: Number of transfers in must match the number of transfers out"
                self.model += lpSum([t_in[(p.id, g)] for p in P]) == lpSum([t_out[(p.id, g)] for p in P]), name

                name = f"GW {g}: Squad value must be within budget"
                self.model += lpSum([z[(p.id, g)] * p.cost for p in P]) <= b_r, name

                # name = f"GW {g}: Bank balance equals previous bank +/- transfer costs"
                # self.model += b[g - 1] + lpSum([t_out[(p.id, g)] * p.cost - t_in[(p.id, g)] * p.cost]
                #                                for p in P) == b[g], name

                # name = f"GW {g}: Bank balance remaining must always be greater than or equal to 0"
                # self.model += b[g] >= 0, name

            for r in R:
                # Constraint on the number of players from each position required
                name = f"GW {g}: Role {r} requires {n_r[r]} players"
                self.model += lpSum([z[(p.id, g)] for p in P_r[r]]) == n_r[r], name

                # Minimum number of players required for each role in starting 11
                name = f"GW {g}: At least {l_r[r]} of role {r} must start"
                self.model += lpSum([x[(p.id, g)]] for p in P_r[r]) >= l_r[r], name

                # Maximum number of players required for each role in starting 11
                name = f"GW {g}: At most {u_r[r]} of role {r} can start"
                self.model += lpSum([x[(p.id, g)]] for p in P_r[r]) <= u_r[r], name

            for c in C:
                # Maximum of 3 players from each club
                name = f"GW {g}: Max 3 players from club {c}"
                self.model += lpSum([z[(p.id, g)]] for p in P if p.club_id == c.id) <= 3, name

            for p in P:
                # Squad must be made up of starting 11 and 4 on the bench
                name = f"GW {g}: Player {p.id} is in the squad of 15"
                self.model += x[(p.id, g)] + y[(p.id, g)] == z[(p.id, g)], name

                name = f"GW {g}: Player {p.id} cannot be captain and vice captain during the same gameweek"
                self.model += cc[(p.id, g)] + vc[(p.id, g)] <= 1, name

                name = f"GW {g}: If player {p.id} is captain, he must be in the starting 11"
                self.model += x[(p.id, g)] >= cc[(p.id, g)], name

                name = f"GW {g}: If player {p.id} is vice captain, he must be in the starting 11"
                self.model += x[(p.id, g)] >= vc[(p.id, g)], name

                if g > self.gameweek:
                    # Track when a player is transferred in or out based on the previous gameweek's selection
                    name = f"GW {g}: Track player {p.id}'s transfers"
                    self.model += z[(p.id, g)] - z[(p.id, g - 1)] + t_out[(p.id, g)] == t_in[(p.id, g)], name

                if g == 0:
                    name = f"GW {g}: Player {p.id} in initial squad must be transferred in"
                    self.model += t_in[(p.id, g)] == z[(p.id, g)], name

                    t_out[(p.id, g)].setInitialValue(0)
                    t_out[(p.id, g)].fixValue()

        # ----------------------------------------
        # Objective Function
        # --------------------------------------

        points = lpSum([x[(p.id, g)] * self.calculate_score(p, g) for p in P for g in G])
        bench = 0.1 * lpSum([y[(p.id, g)] * self.calculate_score(p, g) for p in P for g in G])
        captain = lpSum([cc[(p.id, g)] * self.calculate_score(p, g) for p in P for g in G])
        vice_captain = 0.5 * lpSum([vc[(p.id, g)] * self.calculate_score(p, g) for p in P for g in G])

        self.model += points + bench + captain + vice_captain

        self.model.solve()
        self.status = LpStatus[self.model.status]
        self.objective_value = lpValue(self.model.objective)
        # ----------------------------------------
        # Store results in fantasy team instance
        # --------------------------------------

        teams = {}
        teams[self.gameweek] = self.team
        for g in G[1:]:
            team = FantasyTeam(g)
            team.bank = lpValue(b[g])
            for p in P:
                if lpValue(cc[(p.id, g)]):
                    team.captain = p

                if lpValue(vc[(p.id, g)]):
                    team.vice_captain = p

                if lpValue(t_in[(p.id, g)]):
                    team.transfers_in.append(p)

                if lpValue(t_out[(p.id, g)]):
                    team.transfers_out.append(p)

                if lpValue(x[(p.id, g)]):
                    team.starting.append(p.id)
                    team.players[p.id] = p

                if lpValue(y[(p.id, g)]):
                    team.bench.append(p.id)
                    team.players[p.id] = p

            teams[g] = team
        return teams

    def calculate_score(self, player, gw) -> float:
        return float(player.selected_by_percent) * player.chance_of_playing
