"""Implements dynamic programming to compute the expected HP loss of every state action pair"""

import csv
from fractions import Fraction

from card import Bash, Defend, Strike
from character.enemies import FuzzyWurmCrawler
from character.player import Ironclad
from fight import Fight

CARDS = {"strike": Strike(), "defend": Defend(), "bash": Bash()}


# Read the table from file if it exists
def load_dp_table(fname: str):

    def is_valid(key: tuple, value: dict[int, Fraction]) -> bool:
        return len(key) == 175 and sum(value.values()) == Fraction(1)

    new_table: dict[tuple, dict[int, Fraction]] = {}
    with open(fname, "r") as file:
        reader = csv.reader(file, delimiter=",")
        for row in reader:
            state_action_pair, data = map(
                lambda field: eval(field, {"__builtins__": {}, "Fraction": Fraction}),
                row,
            )

            if is_valid(state_action_pair, data):
                new_table[state_action_pair] = data

    return new_table


# Write the table to file
def dump_dp_table(table: dict[tuple, dict[int, Fraction]], fname: str):
    with open(fname, "w") as file:
        writer = csv.writer(file, delimiter=",")
        for state_action_pair, hp_losses in table.items():
            writer.writerow((state_action_pair, hp_losses))


if __name__ == "__main__":
    dp_table: dict[tuple, dict[int, Fraction]] = load_dp_table("./data/dp_data.csv")
    player = Ironclad(
        name="Player",
        player_turn_callback=lambda fight: True,
    )
    enemy = FuzzyWurmCrawler(name="Enemy", hp=59)
    fight = Fight(player=player, enemies=[enemy])
    fight.search_player_turn_start(dp_table, hp_limit=39)
    dump_dp_table(dp_table, "./data/dp_data.csv")
