"""Implements dynamic programming to compute the expected HP loss of every state action pair"""

import csv
from fractions import Fraction
from time import perf_counter

from card import Bash, Defend, Strike
from character.enemies import FuzzyWurmCrawler
from character.player import Ironclad
from fight import Fight

CARDS = {"strike": Strike(), "defend": Defend(), "bash": Bash()}


# Read the table from file if it exists
def load_dp_table(fname: str):

    def is_valid(key: tuple, value: dict[int, Fraction]) -> bool:
        return len(key) == 175 and sum(value.values()) == Fraction(1)

    new_table: dict[tuple, tuple[dict[int, Fraction], bool]] = {}
    with open(fname, "r") as file:
        reader = csv.reader(file, delimiter=",")
        for row in reader:
            state_action_pair, data = map(
                lambda field: eval(field, {"__builtins__": {}, "Fraction": Fraction}),
                row,
            )

            if is_valid(state_action_pair, data):
                new_table[state_action_pair] = (data, True)

    return new_table


# Write the table to file
def dump_dp_table(table: dict[tuple[int, ...], tuple[dict[int, Fraction], bool]], fname: str):
    with open(fname, "w") as file:
        writer = csv.writer(file, delimiter=",")
        for state_action_pair, data in table.items():
            hp_losses, search_complete = data
            if search_complete:
                writer.writerow((state_action_pair, hp_losses))


if __name__ == "__main__":
    dp_table: dict[tuple[int, ...], tuple[dict[int, Fraction], bool]] = load_dp_table("./data/dp_data.csv")
    cache_size = len(dp_table)

    # Configure your search below
    player = Ironclad(
        name="Player",
        player_turn_callback=lambda fight: True,
    )
    enemy = FuzzyWurmCrawler(name="Enemy", hp=58)
    fight = Fight(player=player, enemies=[enemy])

    interrupted = True
    start = perf_counter()
    try:
        hp_losses, search_complete = fight.search_player_turn_start(dp_table, hp_limit=20)
        interrupted = False
    finally:
        end = perf_counter()
        complete = sum([value[1] for value in dp_table.values()])

        print("=" * 30 + "RESULTS" + "=" * 30)
        print(f"{"ACTIONS EXPLORED":30}| {len(dp_table)} ({complete/len(dp_table):.2%} fully)")
        print(f"{"TIME ELAPSED":30}| {end - start:.3f}s")
        print(f"{"NEW FULLY EXPLORED ACTIONS":30}| {complete - cache_size}")

        if interrupted:
            print("Search was terminated early, writing partial results to file")
        else:
            print(f"{"EXPECTED HP LOSS":30}| {sum([loss * prob for loss, prob in hp_losses.items()]):2.2f}")
            print(f"{"FULL PROBABILITY DISTRIBUTION":30}| {hp_losses}")

            if search_complete:
                print(
                    "Search complete! The optimal strategy can be determined entirely from fully-explored search paths."
                )
            else:
                print(
                    "Search incomplete - the optimal strategy depends on some unexplored search paths. Please rerun this search with a lower hp_limit. "
                )

        dump_dp_table(dp_table, "./data/dp_data.csv")
