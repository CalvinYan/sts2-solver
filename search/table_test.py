import os
from fractions import Fraction

from card import Defend, Strike
from search.table import QTable


def test_qtable_round_trip():
    data = {((0, 1, 2, 3, 4), (0, 0)): {0: Fraction(1, 3), 2: Fraction(1, 3), 4: Fraction(1, 3)}}
    table = QTable(data)

    fname = "tmp_qtable_round_trip_test.csv.pkl.gz"
    try:
        table.dump(fname)
        new_table = QTable.load(fname)

        assert new_table == table
    finally:
        os.remove(fname)


def test_qtable_append():
    data = {((0, 1, 2, 3, 4), (0, 0)): {0: Fraction(1, 3), 2: Fraction(1, 3), 4: Fraction(1, 3)}}
    table = QTable(data)

    fname = "tmp_qtable_round_trip_test.csv.pkl.gz"
    try:
        table.dump(fname)

        new_data = {
            ((0, 1, 2, 3, 4), (1,)): {0: Fraction(1, 2), 5: Fraction(1, 2)},
            ((5, 6, 7, 8, 9), (0, 0)): {3: Fraction(1)},
        }
        new_table = QTable(new_data)
        new_table.append(fname)

        combined_data = {
            ((0, 1, 2, 3, 4), (0, 0)): {0: Fraction(1, 3), 2: Fraction(1, 3), 4: Fraction(1, 3)},
            ((0, 1, 2, 3, 4), (1,)): {0: Fraction(1, 2), 5: Fraction(1, 2)},
            ((5, 6, 7, 8, 9), (0, 0)): {3: Fraction(1)},
        }
        combined_table = QTable(combined_data)

        print(combined_table)
        print(QTable.load(fname))

        assert combined_table == QTable.load(fname)
    finally:
        os.remove(fname)


def test_qtable_actions_for():
    data = {
        ((0,), (Strike().id, 0)): {8: Fraction(1)},
        ((1,), (Strike().id,)): {0: Fraction(1)},
        ((0,), (Defend().id,)): {4: Fraction(1, 2), 9: Fraction(1, 3), 15: Fraction(1, 6)},
    }
    table = QTable(data)

    expected = {
        (Strike().id, 0): {8: Fraction(1)},
        (Defend().id,): {4: Fraction(1, 2), 9: Fraction(1, 3), 15: Fraction(1, 6)},
    }
    assert expected == table.actions_for((0,))
