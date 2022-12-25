import pulp
from setup import setup

API_URL = 'https://fantasy.premierleague.com/api/bootstrap-static/'
FIXTURE_URL = 'https://fantasy.premierleague.com/api/fixtures/?future=1'

league, squad = setup(API_URL, FIXTURE_URL)
players = league.get_players()
model = pulp.LpProblem(name='fantasypl', sense=pulp.LpMaximize)


# ----------------------------------------
# Sets & Subsets
# ---------------------------------------

# Set of players
P = range(len(league.get_players()))

# Set of clubs
C = league.get_clubs().keys()

# Set of gameweeks
G = range(3)

# Set of roles i.e GK, DF, MF, FW
R = range(4)

# Set of players, sorted by their role
P_r = {
    0: league.get_goalkeepers(),
    1: league.get_defenders(),
    2: league.get_midfielders(),
    3: league.get_forwards()
}

# ----------------------------------------
# Parameters
# ---------------------------------------

# Budget
b = 100

# Number of players of role r required to make up a squad of 15
n_r = [2, 5, 5, 3]

# Lower bound on the number of players of role r that must be in the starting 11
l_r = [1, 3, 3, 1]

# Upper bound on the number of players of role r that must be in the starting 11
u_r = [1, 5, 5, 3]

# ----------------------------------------
# Decision Variables
# ---------------------------------------

# Player p is in the starting 11 in gameweek g
x = pulp.LpVariable.dicts("Starting", ((p, g) for p in P for g in G), cat=pulp.LpBinary)

# player p is on the bench in gameweek g
y = pulp.LpVariable.dicts("Benched", ((p, g) for p in P for g in G), cat=pulp.LpBinary)

# Player p has been selected in gameweek g (Derived from x and y)
z = pulp.LpVariable.dicts("Selected", ((p, g) for p in P for g in G), cat=pulp.LpBinary)

# Player p is transferred into the squad in gameweek g
t_in = pulp.LpVariable.dicts("Transfer_In", ((p, g) for p in P for g in G), cat=pulp.LpBinary)

# Player p is transferred out of the squad in gameweek g
t_out = pulp.LpVariable.dicts("Transfer_Out", ((p, g) for p in P for g in G), cat=pulp.LpBinary)

# Additional transfers required in gameweek g (each one incurs a penalty of minus 4 points)
a = pulp.LpVariable.dicts("Additional_Transfers", (g for g in G), lowBound=0, cat=pulp.LpInteger)

# Player p is captained in gameweek g
f = pulp.LpVariable.dicts("Captained", ((p, g) for p in P for g in G), cat=pulp.LpBinary)

# Player p is vice captain during gameweek g
h = pulp.LpVariable.dicts("Viced", ((p, g) for p in P for g in G), cat=pulp.LpBinary)

# Triple captain chip is used during gameweek g
alpha = pulp.LpVariable.dicts("TC", (g for g in G), cat=pulp.LpBinary)

# Bench boost chip is used during gameweek g
# beta = pulp.LpVariable.dicts("BB", ((g) for g in G), cat=pulp.LpBinary)

# ----------------------------------------
# Objective Function
# ---------------------------------------

# Expected number of points from each player selected
points = pulp.lpSum([x[(players[p].get_id(), g)] * players[p].get_total_points()
                    * players[p].get_chance_of_playing()] for p in P for g in G)

bench = pulp.lpSum([y[(players[p].get_id(), g)] * players[p].get_total_points() *
                   0.1 * players[p].get_chance_of_playing()] for p in P for g in G)

# Captain gets x2 points
captain = pulp.lpSum([(f[(players[p].get_id(), g)] + alpha[g]) * players[p].get_total_points()] for p in P for g in G)

# Vice captain has a small chance of being selected
vice = pulp.lpSum([h[(players[p].get_id(), g)] * players[p].get_total_points() * 0.1] for p in P for g in G)

# Deduct any additional transfers
transfers = pulp.lpSum([a[g] * 4 for g in G])

model += points + bench + captain + vice - transfers, "Objective Function"

# ----------------------------------------
# Constraints
# ---------------------------------------

# Only one triple captain chip can be used
model += pulp.lpSum([alpha[g] for g in G]) <= 1, "Only one triple captain may be played"

# Only one bench boost chip can be used
# model += pulp.lpSum([beta[g] for g in G]) <= 1, "Only one bench boost may be played"

for g in G:
    for p in P:
        # Player p was selected during gameweek g
        model += x[(p, g)] + y[(p, g)] == z[(p, g)], f"GW {g}: Player {p} was selected"

        # Captain must be in the starting 11
        model += x[(p, g)] >= f[(p, g)], f"GW {g}: Captain {p} must be in starting 11"

        # Vice captain must be in the starting 11
        model += x[(p, g)] >= h[(p, g)], f"GW {g}: VC {p} must be in starting 11"

        # A player cannot be both captain and vice captain in the same gameweek
        model += f[(p, g)] + h[(p, g)] <= 1, f"GW {g}: Player {p} cannot be captain and VC"

        if g == 0:
            # All players selected in 1st gameweek are transferred in
            model += z[(p, g)] == t_in[(p, g)], f"GW {g}: Player {p} transferred in during gameweek 1"

            # No players may be transferred out during 1st gameweek
            model += t_out[(p, g)] == 0, f"GW {g}: Player {p} not transferred out during gameweek 1"
        else:
            # Track which players are transferred in and out each gameweek
            model += pulp.lpSum([z[(p, g)] - z[(p, g - 1)]]) + t_out[(p, g)
                                                                     ] == t_in[(p, g)], f"GW {g}: Player {p} transferred"

            # A player cannot be both transferred in and out in the same gameweek
            model += pulp.lpSum(t_in[(p, g)] + t_out[(p, g)]
                                ) <= 1, f"GW {g}: Player {p} cannot be transferred in and out"

    if g == 0:
        # No additional transfers during the first gameweek
        model += a[g] == 0, f"GW {g}: No additional transfers"
    elif g == 1:
        # The second gameweek you may only make one free transfer
        model += pulp.lpSum([t_in[(p, g)] for p in P]) <= 1 + a[g], f"GW {g}: Max 1 transfers in during gameweek 2"
        model += pulp.lpSum([t_out[(p, g)] for p in P]) <= 1 + a[g], f"GW {g}: Max 1 transfers out during gameweek 2"
    elif g > 1:
        # The number of free transfers depend on the number used in the previous gameweek
        model += pulp.lpSum([t_in[(p, g)] for p in P]) <= 2 - pulp.lpSum([t_in[(p, g - 1)]]
                                                                         for p in P) + a[g], f"GW {g}: Max 2 transfers in"
        model += pulp.lpSum([t_out[(p, g)] for p in P]) <= 2 - pulp.lpSum([t_out[(p, g - 1)]]
                                                                          for p in P) + a[g], f"GW {g}: Max 2 transfers out"

    for r in R:
        # 15 Players made up of 2GK, 5DF, 5MF, 3FW
        model += pulp.lpSum([z[(p.get_id(), g)] for p in P_r[r]]
                            ) == n_r[r], f"GW {g}: Role {r} requires {n_r[r]} players"

        # Minimum players of role r required in a starting 11
        model += pulp.lpSum([x[(p.get_id(), g)]]
                            for p in P_r[r]) >= l_r[r], f"GW {g}: At least {l_r[r]} of role {r} must start"

        # Maximum players of role r required in a starting 11
        model += pulp.lpSum([x[(p.get_id(), g)]]
                            for p in P_r[r]) <= u_r[r], f"GW {g}: At most {u_r[r]} of role {r} can start"

    for c in C:
        # Maximum 3 players from each club in squad
        model += pulp.lpSum([z[(p, g)]] for p in P if players[p].get_club()
                            == c) <= 3, f"GW {g}: Max 3 players from club {c}"

    # Budget constraint
    model += pulp.lpSum([z[(p, g)] * players[p].get_value()] for p in P) <= b, f"GW {g}: Budget constraint"

    # The starting eleven must have eleven players...
    model += pulp.lpSum([x[(p, g)] for p in P]) == 11, f"GW {g}: 11 players must start"

    # Only one captain may be selected each gameweek
    model += pulp.lpSum([f[(p, g)]] for p in P) == 1, f"GW {g}: Captain one player per gameweek"

    # Only one vice captain may be selected each gameweek
    model += pulp.lpSum([h[(p, g)]] for p in P) == 1, f"GW {g}: Vice Captain one player per gameweek"

    # Only one chip can be played per gameweek
    # model += pulp.lpSum([alpha[g] + beta[g]]) <= 1, f"GW {g}: Only one chip can be played at a time"

# ----------------------------------------
# Solve & Display
# ---------------------------------------

model.solve()
for g in G:
    squad.set_chip('TC', pulp.value(alpha[g]) == 1, g)

    for p in players:
        if pulp.value(f[(p.get_id(), g)]):
            squad.set_captain(p, g)

        if pulp.value(h[(p.get_id(), g)]):
            squad.set_vice_captain(p, g)

        if pulp.value(x[(p.get_id(), g)]):
            squad.add_player(p, g)

        if pulp.value(y[(p.get_id(), g)]):
            squad.add_to_bench(p, g)

        if pulp.value(t_in[(p.get_id(), g)]):
            squad.transfer_in(p, g)

        if pulp.value(t_out[(p.get_id(), g)]):
            squad.transfer_out(p, g)

squad.display()
print("\nStatus:", pulp.LpStatus[model.status])
print("Value:", pulp.value(model.objective))
