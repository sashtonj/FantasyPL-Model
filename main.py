from typing import Dict
from premierleague import PremierLeague
from model import Model
from fantasyteam import FantasyTeam
from setup import setup_premier_league, setup_fantasy_team

pl: PremierLeague = setup_premier_league(PremierLeague())
team: FantasyTeam = setup_fantasy_team(pl)

model = Model(pl, team)
teams: Dict[int, FantasyTeam] = model.solve(3)

if model.status == 'Infeasible':
    print("Problem is infeasible")
else:
    for gw in range(pl.current_gw, pl.current_gw + 4):
        print(f"\n------------\nGameweek: {gw}\n------------")
        teams[gw].display_gameweek()
