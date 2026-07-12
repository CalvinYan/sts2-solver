"""Implements dynamic programming to compute the expected HP loss of every state action pair"""

import gzip
import pickle
from fractions import Fraction
from time import perf_counter

from card import Bash, Defend, Strike
from character.enemies import Nibbit, Seapunk, ShrinkerBeetle
from character.player import Ironclad
from fight import Fight

CARDS = {"strike": Strike(), "defend": Defend(), "bash": Bash()}


# Read the table from file if it exists
def load_dp_table(fname: str):

    start = perf_counter()
    with gzip.open(fname, mode="rb") as f:
        new_table = pickle.load(f)
    dp_table = {k: (v, True) for k, v in new_table.items()}
    end = perf_counter()
    print(f"Loaded {len(dp_table)} csv.pkl.gzip rows in {end - start} seconds")


# Write the table to file
def dump_dp_table(table: dict[tuple[int, ...], tuple[dict[int, Fraction], bool]], fname: str):
    data = {k: v[0] for k, v in table.items() if v[1]}
    with gzip.open(fname, mode="wb", compresslevel=6) as f:
        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)


def search(fight: Fight, dp_table: dict[tuple[int, ...], tuple[dict[int, Fraction], bool]], name: str = "") -> None:
    cache_size = len(dp_table)
    print(f"Searching fight {name}:")

    interrupted = True
    start = perf_counter()
    try:
        hp_losses, search_complete = fight.search_player_turn_start(dp_table, hp_limit=24)
        interrupted = False
    finally:
        end = perf_counter()
        complete = sum([value[1] for value in dp_table.values()])

        print("=" * 30 + "RESULTS" + "=" * 30)
        print(f"{"TIME ELAPSED":30}| {end - start:.3f}s")
        print(f"{"NEW FULLY EXPLORED ACTIONS":30}| {complete - cache_size}")

        if interrupted:
            print("Search was terminated early, writing partial results to file")
            dump_dp_table(dp_table, "./data/dp_data.csv")
            exit()
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


if __name__ == "__main__":
    for enemy_cls, name in zip([Nibbit, Seapunk, ShrinkerBeetle], ["nibbit", "seapunk", "shrinker_beetle"]):
        dp_table: dict[tuple[int, ...], tuple[dict[int, Fraction], bool]] = load_dp_table(
            f"./data/solver/ironclad-base/{name}.csv"
        )

        for enemy_hp in range(enemy_cls.min_hp, enemy_cls.max_hp + 1):
            player = Ironclad(name="Player")
            enemy = enemy_cls(name="Enemy", hp=enemy_hp)
            fight = Fight(player=player, enemies=[enemy])
            search(fight, dp_table, name=f"Ironclad vs {enemy_hp}-HP {enemy_cls.__name__}")

        dump_dp_table(dp_table, f"./data/solver/ironclad-base/{name}.csv")
