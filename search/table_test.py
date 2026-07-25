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


def test_qtable_reports_size_and_membership():
    state_action = ((0, 1, 2, 3, 4), (Strike().id, 0))
    table = QTable({state_action: {8: Fraction(1)}})

    assert len(table) == 1
    assert state_action in table
    assert ((0, 1, 2, 3, 4), (Defend().id,)) not in table
    assert list(table.values()) == [{8: Fraction(1)}]


def test_qtable_update_merges_and_overwrites():
    shared_key = ((0, 1, 2, 3, 4), (Strike().id, 0))
    table = QTable({shared_key: {8: Fraction(1)}})
    other = QTable({shared_key: {6: Fraction(1)}, ((5,), (Defend().id,)): {0: Fraction(1)}})

    table.update(other)

    assert len(table) == 2
    assert table[shared_key] == {6: Fraction(1)}
    assert table[((5,), (Defend().id,))] == {0: Fraction(1)}


def test_qtable_load_creates_a_missing_file():
    fname = "tmp_qtable_missing_test.csv.pkl.gz"
    assert not os.path.exists(fname)
    try:
        table = QTable.load(fname)

        # Loading a table that does not exist yet starts an empty one and writes it out
        assert len(table) == 0
        assert os.path.exists(fname)
        assert QTable.load(fname) == table
    finally:
        os.remove(fname)
