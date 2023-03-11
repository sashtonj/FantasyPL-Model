from pulp import LpVariable, LpProblem, LpStatus, LpMaximize, LpBinary, LpInteger, lpSum, value as lpValue
from premierleague import PremierLeague
from premierleague.role import Role
from fantasyteam import FantasyTeam

MANAGER_ID = "6082478"


class FantasyModel:

    def __init__(self, pl: PremierLeague, team: FantasyTeam) -> None:
        self.pl = pl
        self.team = team
        self.model = LpProblem(name='fantasypl', sense=LpMaximize)

    def solve(self, horizon_len: int, history_len: int) -> None:
        self.horizon_len = horizon_len + 2
        self.history_len = history_len

        # ----------------------------------------
        # Sets & Subsets
        # ---------------------------------------
        # Set of players
        P = self.pl.get_players().values()

        # Set of clubs
        C = self.pl.clubs.values()

        # Set of gameweeks
        G = range(self.pl.current_gw, self.pl.current_gw + self.horizon_len)

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

        # Additional transfers that will incur a cost
        # a = LpVariable.dicts("Additional_transfers", (g for g in G), lowBound=0, cat=LpInteger)

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

                # No transfers in current gameweek
                for p in P:
                    t_in[(p.id, g)].setInitialValue(0)
                    t_in[(p.id, g)].fixValue
                    t_out[(p.id, g)].setInitialValue(0)
                    t_out[(p.id, g)].fixValue

                continue

            # self.model += a[g] == 0, f"GW {g}: No additional transfers allowed"

            # A captain must be selected for each gameweek to earn double points
            name = f"GW {g}: Must have a captain selected"
            self.model += lpSum([cc[(p.id, g)] for p in P]) == 1, name

            # A vice captain must be selected for each gameweek to earn double points
            name = f"GW {g}: Must have a vice captain selected"
            self.model += lpSum([vc[(p.id, g)] for p in P]) == 1, name

            # Calculate budget for next week = previous budget + sell on fees
            name = f"GW {g}: Budget equals previous budget plus any sell on fees"
            # self.model += b[g - 1] + lpSum([t_out[(p, g)] * get_sell_on_fee(P[p]) for p in P]) == b[g], name

            # Make sure the value of the squad is within our budget
            name = f"GW {g}: Budget constraint"
            self.model += lpSum([z[(p.id, g)] * p.cost for p in P]) <= self.team.squad_value, name

            # The number of free transfers in is either one or two (depends on the previous gameweek)
            if g == self.pl.current_gw + 1:
                # Wild Card
                max_transfers = 15
            elif g == self.pl.current_gw + 2:
                max_transfers = 1
            else:
                max_transfers = 2 - lpSum([t_in[(p.id, g - 1)] for p in P])

            name = f"GW {g}: Maximum 2 free transfers in to the team during each gameweek"
            self.model += lpSum([t_in[(p.id, g)] for p in P]) <= max_transfers, name

            # The number of free transfers out is either one or two (depends on the previous gameweek)
            if g == self.pl.current_gw + 1:
                # Wild Card
                max_transfers = 15
            elif g == self.pl.current_gw + 2:
                max_transfers = 1
            else:
                max_transfers = 2 - lpSum([t_out[(p.id, g - 1)] for p in P])

            name = f"GW {g}: Maximum 2 free transfers out of the team during each gameweek"
            self.model += lpSum([t_out[(p.id, g)] for p in P]) <= max_transfers, name

            # The starting eleven must have eleven players...
            name = f"GW {g}: 11 players must start"
            self.model += lpSum([x[(p.id, g)] for p in P]) == 11, name

            name = f"GW {g}: Number of transfers in must match the number of transfers out"
            self.model += lpSum([t_in[(p.id, g)] for p in P]) == lpSum([t_out[(p.id, g)] for p in P]), name

            for p in P:
                # Indicates player is in the squad of 15
                name = f"GW {g}: Player {p.id} is in the squad of 15"
                self.model += x[(p.id, g)] + y[(p.id, g)] == z[(p.id, g)], name

                # Player cannot be captain and vice captain at the same time
                name = f"GW {g}: Player {p.id} cannot be captain and vice captain during the same gameweek"
                self.model += cc[(p.id, g)] + vc[(p.id, g)] <= 1, name

                # Ensure the captain is in the starting 11
                name = f"GW {g}: If player {p.id} is captain, he must be in the starting 11"
                self.model += x[(p.id, g)] >= cc[(p.id, g)], name

                # Ensure the vice captain is in the starting 11
                name = f"GW {g}: If player {p.id} is vice captain, he must be in the starting 11"
                self.model += x[(p.id, g)] >= vc[(p.id, g)], name

                # Prevent players from being transferred in and out in the same gameweek
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
                # Maximum of 3 players from each club in squad
                name = f"GW {g}: Max 3 players from club {c}"
                self.model += lpSum([z[(p.id, g)]] for p in P if p.club_id == c.id) <= 3, name

        points = lpSum([x[(p.id, g)] * self.calculate_score(p, g) for p in P for g in G])
        bench = 0.1 * lpSum([y[(p.id, g)] * self.calculate_score(p, g) for p in P for g in G])
        captain = lpSum([cc[(p.id, g)] * self.calculate_score(p, g) for p in P for g in G])

        self.model += points + bench + captain

        self.model.solve()
        self.status = LpStatus[self.model.status]
        self.objective_value = lpValue(self.model.objective)

        for g in range(self.pl.current_gw + 1, self.pl.current_gw + self.horizon_len):
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

        return round(player.chance_of_playing * points * this_gw, 2)
