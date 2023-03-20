import sys
from pulp import LpVariable, LpProblem, LpStatus, LpMaximize, LpBinary, LpInteger, lpSum, value as lpValue
from premierleague import PremierLeague
from premierleague.role import Role
from fantasyteam import FantasyTeam


class FantasyModel:

    def __init__(self, pl: PremierLeague, team: FantasyTeam) -> None:
        self.pl = pl
        self.team = team
        self.model = LpProblem(name='fantasypl', sense=LpMaximize)

    def solve(self, horizon_len: int, history_len: int, max_gw: int = 38) -> None:
        self.horizon_len = horizon_len
        self.history_len = history_len

        if self.pl.current_gw + self.horizon_len > max_gw:
            sys.exit(f"Horizon length of {self.horizon_len} exceed maximum gameweek of {max_gw}")

        # ----------------------------------------
        # Sets & Subsets
        # ---------------------------------------
        # Set of players
        P = self.pl.get_players().values()

        # Set of clubs
        C = self.pl.clubs.values()

        # Set of gameweeks
        G = range(self.pl.current_gw, self.pl.current_gw + self.horizon_len + 1)

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
        b_r = self.team.bank

        # ----------------------------------------
        # Decision Variables
        # ---------------------------------------

        # Player p is in the starting 11 in gameweek g
        x = LpVariable.dicts("Starting", ((p.id, g) for p in P for g in G), cat=LpBinary)

        # player p is on the bench in gameweek g
        y = LpVariable.dicts("Benched", ((p.id, g) for p in P for g in G), cat=LpBinary)

        # Player p has been selected in gameweek g (Derived from x and y)
        z = LpVariable.dicts("Selected", ((p.id, g) for p in P for g in G), cat=LpBinary)

        # Player p has been transferred in during gameweek g
        t_in = LpVariable.dicts("Transferred_in", ((p.id, g) for p in P for g in G), cat=LpBinary)

        # Player p has been transferred in during gameweek g
        t_out = LpVariable.dicts("Transferred_out", ((p.id, g) for p in P for g in G), cat=LpBinary)

        # Indicates that zero transfers were conducted during gameweek g: {0: transfers, 1: zero transfers}
        zero_t = LpVariable.dicts("Max_transfers", (g for g in G), cat=LpBinary)

        # Player p is club captain during gameweek g
        cc = LpVariable.dicts("Captain", ((p.id, g) for p in P for g in G), cat=LpBinary)

        # Player p is vice captain during gameweek g
        vc = LpVariable.dicts("Vice_captain", ((p.id, g) for p in P for g in G), cat=LpBinary)

        # Our budget for each week
        b = LpVariable.dicts("Budget", (g for g in G), cat=LpInteger)

        # ----------------------------------------
        # Constraints
        # --------------------------------------
        for g in G:

            if g == self.pl.current_gw:
                # Current gameweek => set initial budgets, squad, and transfers etc.

                # Set initial budget
                b[g].setInitialValue(b_r)
                b[g].fixValue()

                # Set initial squad
                for p in self.team.players[g].values():
                    z[(p.id, g)].setInitialValue(1)
                    z[(p.id, g)].fixValue()

                # Set current Captain
                cc[(self.team.captain[g].id, g)].setInitialValue(1)
                cc[(self.team.captain[g].id, g)].fixValue

                # Set current vice Captain
                vc[(self.team.vice_captain[g].id, g)].setInitialValue(1)
                vc[(self.team.vice_captain[g].id, g)].fixValue

                for p in self.team.transfers_in.get(g, []):
                    t_in[(p.id, g)].setInitialValue(1)
                    t_in[(p.id, g)].fixValue()

                for p in self.team.transfers_out.get(g, []):
                    t_out[(p.id, g)].setInitialValue(1)
                    t_out[(p.id, g)].fixValue()

                continue

            name = f"GW {g}: Must have a captain selected"
            self.model += lpSum([cc[(p.id, g)] for p in P]) == 1, name

            name = f"GW {g}: Must have a vice captain selected"
            self.model += lpSum([vc[(p.id, g)] for p in P]) == 1, name

            name = f"GW {g}: Squad value must be within our budget"
            self.model += lpSum([z[(p.id, g)] * p.cost for p in P]) <= self.team.squad_value, name

            name = f"GW {g}: Calculate whether any transfers occurred in the previous gameweek"
            self.model += lpSum([t_in[(p.id, g - 1)] for p in P]) <= 2 * (1 - zero_t[g]), name

            # name = f"GW {g}: The max number of transfers out for this gw based on the transfers from last week"
            # self.model += lpSum([t_out[(p.id, g - 1)] for p in P]) <= 2 * (1 - zero_t[g]), name

            name = f"GW {g}: Maximum of 2 free transfers in to the team during each gameweek"
            self.model += lpSum([t_in[(p.id, g)] for p in P]) <= 1 + zero_t[g], name

            name = f"GW {g}: Maximum of 2 free transfers out of the team during each gameweek"
            self.model += lpSum([t_out[(p.id, g)] for p in P]) <= 1 + zero_t[g], name

            name = f"GW {g}: Number of transfers in must match the number of transfers out"
            self.model += lpSum([t_in[(p.id, g)] for p in P]) == lpSum([t_out[(p.id, g)] for p in P]), name

            name = f"GW {g}: Starting 11 must have 11 players..."
            self.model += lpSum([x[(p.id, g)] for p in P]) == 11, name

            for p in P:
                name = f"GW {g}: Player {p.id} is in the squad of 15"
                self.model += x[(p.id, g)] + y[(p.id, g)] == z[(p.id, g)], name

                name = f"GW {g}: Player {p.id} cannot be captain and vice captain during the same gameweek"
                self.model += cc[(p.id, g)] + vc[(p.id, g)] <= 1, name

                name = f"GW {g}: If player {p.id} is captain, he must be in the starting 11"
                self.model += x[(p.id, g)] >= cc[(p.id, g)], name

                name = f"GW {g}: If player {p.id} is vice captain, he must be in the starting 11"
                self.model += x[(p.id, g)] >= vc[(p.id, g)], name

                name = f"GW {g}: Player {p.id} cannot be transferred in and out in the same gameweek"
                self.model += t_in[(p.id, g)] + t_out[(p.id, g)] <= 1, name

                # Track when a player is transferred in or out based on the previous gameweek's selection
                name = f"GW {g}: Track player {p.id}'s transfers"
                self.model += z[(p.id, g)] - z[(p.id, g - 1)] + t_out[(p.id, g)] == t_in[(p.id, g)], name

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
                name = f"GW {g}: Max 3 players from club {c}"
                self.model += lpSum([z[(p.id, g)]] for p in P if p.club_id == c.id) <= 3, name

        # ----------------------------------------
        # Objective Function
        # --------------------------------------

        points = lpSum([x[(p.id, g)] * self.calculate_score(p, g) for p in P for g in G])
        bench = 0.1 * lpSum([y[(p.id, g)] * self.calculate_score(p, g) for p in P for g in G])
        captain = lpSum([cc[(p.id, g)] * self.calculate_score(p, g) for p in P for g in G])

        self.model += points + bench + captain

        self.model.solve()
        self.status = LpStatus[self.model.status]
        self.objective_value = lpValue(self.model.objective)

        # ----------------------------------------
        # Store results in fantasy team instance
        # --------------------------------------

        for g in range(self.pl.current_gw + 1, self.pl.current_gw + self.horizon_len + 1):

            for p in self.pl.get_players().values():
                if lpValue(cc[(p.id, g)]):
                    self.team.captain[g] = p

                if lpValue(vc[(p.id, g)]):
                    self.team.vice_captain[g] = P

                if lpValue(t_in[(p.id, g)]):
                    self.team.transfers_in.setdefault(g, []).append(p)

                if lpValue(t_out[(p.id, g)]):
                    self.team.transfers_out.setdefault(g, []).append(p)

                if lpValue(x[(p.id, g)]):
                    self.team.starting.setdefault(g, []).append(p.id)
                    self.team.players.setdefault(g, {})[p.id] = p

                if lpValue(y[(p.id, g)]):
                    self.team.bench.setdefault(g, []).append(p.id)
                    self.team.players.setdefault(g, {})[p.id] = p

    def calculate_score(self, player, gw) -> float:
        """
        Used to calculate how many points we expect a player to earn during each gameweek
        """
        club = self.pl.get_club(player.club_id)
        points = 0
        games = 0

        fixture_multiplier = 0.05
        home_adv = 0.1
        difficulty_multiplier = 0.15

        for g in range(self.pl.current_gw - self.history_len, self.pl.current_gw + 1):
            for gw_points in player.points.get(g, []):
                points += gw_points * (1 - (fixture_multiplier * (self.pl.current_gw - g)))
                games += 1

        points = points / games
        this_gw = 0
        for f in club.fixtures.get(gw, []):
            at_home = f.home_team == club.id
            difficulty = f.home_team_difficulty if at_home else f.away_team_difficulty
            this_gw += 1 - (difficulty_multiplier * difficulty)
            this_gw += home_adv if at_home else 0

        score = round(player.chance_of_playing * points * this_gw, 2)
        if len(player.points.get(gw, [])) == 0:
            # This is the first time we've calculated for this player => Store in the player's instance
            player.add_gameweek_stat(gw, 'points', score)

        return score
