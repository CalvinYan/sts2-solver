"""Implements dynamic programming to compute the expected HP loss of every state action pair"""

import gzip
import pickle
from fractions import Fraction
from pathlib import Path
from time import perf_counter

from card import Bash, Defend, Strike
from character.enemies import (
    FuzzyWurmCrawler,
    Nibbit,
    Seapunk,
    ShrinkerBeetle,
    SludgeSpinner,
)
from character.player import Ironclad, Regent
from fight import Fight

CARDS = {"strike": Strike(), "defend": Defend(), "bash": Bash()}


# Read the table from file, creating an empty one if it doesn't exist
def load_dp_table(fname: str) -> dict[tuple[int, ...], dict[int, Fraction]]:
    file_path = Path(fname)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists() or file_path.stat().st_size == 0:
        dump_dp_table({}, fname)
    with gzip.open(fname, mode="rb") as f:
        dp_table = pickle.load(f)
    return dp_table


# Write the table to file
def dump_dp_table(table: dict[tuple[int, ...], dict[int, Fraction]], fname: str):
    with gzip.open(fname, mode="wb", compresslevel=6) as f:
        pickle.dump(table, f, protocol=pickle.HIGHEST_PROTOCOL)


def append_dp_table(table: dict[tuple[int, ...], dict[int, Fraction]], fname: str):
    merged = load_dp_table(fname)
    merged.update({k: v for k, v in table.items()})
    dump_dp_table(merged, fname)


def search(
    fight: Fight,
    dp_table: dict[tuple[int, ...], tuple[dict[int, Fraction], bool]],
    fname: str,
    name: str = "",
) -> None:
    cache_size = len(dp_table)
    print(f"Searching fight {name}:")

    interrupted = True
    start = perf_counter()
    try:
        hp_losses, search_complete = fight.search_player_turn_start(dp_table)
        interrupted = False
    except BaseException as e:
        tb = e.__traceback__
        raise BaseException("Error running DP search").with_traceback(tb)
    finally:
        end = perf_counter()
        complete = sum([value[1] for value in dp_table.values()])

        print("=" * 30 + "RESULTS" + "=" * 30)
        print(f"{"TIME ELAPSED":30}| {end - start:.3f}s")
        print(f"{"NEW FULLY EXPLORED ACTIONS":30}| {complete - cache_size}")

        if interrupted:
            print("Search was terminated early, writing partial results to file")
            dump_dp_table({k: v[0] for k, v in search_table.items() if v[1]}, fname)
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
    for player_cls, player_name in zip([Ironclad, Regent], ["ironclad", "regent"]):
        for enemy_cls, name in zip(
            [FuzzyWurmCrawler, Nibbit, Seapunk, ShrinkerBeetle, SludgeSpinner],
            ["fuzzy_wurm_crawler", "nibbit", "seapunk", "shrinker_beetle", "sludge_spinner"],
        ):
            fname = f"./data/solver/{player_name}-base/{name}.csv.pkl.gz"
            dp_table: dict[tuple[int, ...], dict[int, Fraction]] = load_dp_table(fname)
            search_table = {k: (v, True) for k, v in dp_table.items()}

            for enemy_hp in range(enemy_cls.min_hp, enemy_cls.max_hp + 1):  # type: ignore
                player = player_cls(name="Player")
                enemy = enemy_cls(name="Enemy", hp=enemy_hp)
                fight = Fight(player=player, enemies=[enemy])
                search(fight, search_table, fname, name=f"{player_cls.__name__} vs {enemy_hp}-HP {enemy_cls.__name__}")

            dp_table = {k: v[0] for k, v in search_table.items() if v[1]}
            dump_dp_table(dp_table, fname)
            # append_dp_table(dp_table, "./data/solver/all.csv.pkl.gz")
