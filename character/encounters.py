from character.enemies import (
    FuzzyWurmCrawler,
    Nibbit,
    Seapunk,
    ShrinkerBeetle,
    SludgeSpinner,
)


def fuzzy_wurm_crawler(verbose: bool = False):
    return [FuzzyWurmCrawler(name="Fuzzy Wurm Crawler", verbose=verbose)]


def nibbit(verbose: bool = False):
    return [Nibbit(name="Nibbit", verbose=verbose)]


def seapunk(verbose: bool = False):
    return [Seapunk(name="Seapunk", verbose=verbose)]


def shrinker_beetle(verbose: bool = False):
    return [ShrinkerBeetle(name="Shrinker Beetle", verbose=verbose)]


def sludge_spinner(verbose: bool = False):
    return [SludgeSpinner(name="Sludge Spinner", verbose=verbose)]
