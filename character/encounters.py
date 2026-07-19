"""Defines the possible encounters for the first fight of the run."""

from character.enemies import (
    FuzzyWurmCrawler,
    Nibbit,
    Seapunk,
    ShrinkerBeetle,
    SludgeSpinner,
    Toadpole,
)
from character.enemies.toadpole import Spiken, Whirl


def fuzzy_wurm_crawler(hp: int | None = None, verbose: bool = False):
    return [FuzzyWurmCrawler(verbose=verbose)] if hp is None else [FuzzyWurmCrawler(hp=hp, verbose=verbose)]


def nibbit(hp: int | None = None, verbose: bool = False):
    return [Nibbit(verbose=verbose)] if hp is None else [Nibbit(hp=hp, verbose=verbose)]


def seapunk(hp: int | None = None, verbose: bool = False):
    return [Seapunk(verbose=verbose)] if hp is None else [Seapunk(hp=hp, verbose=verbose)]


def shrinker_beetle(hp: int | None = None, verbose: bool = False):
    return [ShrinkerBeetle(verbose=verbose)] if hp is None else [ShrinkerBeetle(hp=hp, verbose=verbose)]


def sludge_spinner(hp: int | None = None, verbose: bool = False):
    return [SludgeSpinner(verbose=verbose)] if hp is None else [SludgeSpinner(hp=hp, verbose=verbose)]


def toadpoles(enemy_hps: list[int] = [], verbose: bool = False):
    return (
        [
            Toadpole(name="Toadpole 1", intent=Spiken(), verbose=verbose),
            Toadpole(name="Toadpole 2", intent=Whirl(), verbose=verbose),
        ]
        if not enemy_hps
        else [
            Toadpole(name="Toadpole 1", intent=Spiken(), hp=enemy_hps[0], verbose=verbose),
            Toadpole(name="Toadpole 2", intent=Whirl(), hp=enemy_hps[1], verbose=verbose),
        ]
    )


# All Floor 2 encounters, in a canonical order for iterating over benchmarks.
ALL_ENCOUNTERS = [
    fuzzy_wurm_crawler,
    nibbit,
    seapunk,
    shrinker_beetle,
    sludge_spinner,
]
