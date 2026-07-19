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


def fuzzy_wurm_crawler(verbose: bool = False):
    return [FuzzyWurmCrawler(verbose=verbose)]


def nibbit(verbose: bool = False):
    return [Nibbit(verbose=verbose)]


def seapunk(verbose: bool = False):
    return [Seapunk(verbose=verbose)]


def shrinker_beetle(verbose: bool = False):
    return [ShrinkerBeetle(verbose=verbose)]


def sludge_spinner(verbose: bool = False):
    return [SludgeSpinner(verbose=verbose)]


def toadpoles(verbose: bool = False):
    return [
        Toadpole(name="Toadpole 1", intent=Spiken(), verbose=verbose),
        Toadpole(name="Toadpole 2", intent=Whirl(), verbose=verbose),
    ]


# All Floor 2 encounters, in a canonical order for iterating over benchmarks.
ALL_ENCOUNTERS = [
    fuzzy_wurm_crawler,
    nibbit,
    seapunk,
    shrinker_beetle,
    sludge_spinner,
]
