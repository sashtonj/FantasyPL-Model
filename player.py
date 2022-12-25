class Player:

    def __init__(self, player):
        self.player = player

    def __str__(self):
        return self.get_name()

    def get_id(self):
        return self.player['id']

    def get_name(self):
        return f"{self.get_first_name()} {self.get_surname()}"

    def get_first_name(self):
        return self.player['first_name']

    def get_surname(self):
        return self.player['second_name']

    def get_position(self):
        return self.player['element_type']

    def get_club(self):
        return self.player['team']

    def get_value(self):
        return self.player['now_cost'] / 10

    def get_total_points(self):
        return self.player['total_points']

    def get_chance_of_playing(self):
        if self.player['chance_of_playing_next_round'] is None:
            return 100
        return self.player['chance_of_playing_next_round'] / 100
