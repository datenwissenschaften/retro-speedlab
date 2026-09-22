import numpy as np

from src.game.actions import _B, _NUM_GENESIS_BUTTONS, ACTION_TABLE, ACTIONS


def test_action_table_shape_and_dtype():
    assert ACTION_TABLE.shape == (len(ACTIONS), _NUM_GENESIS_BUTTONS)
    assert ACTION_TABLE.dtype == np.int8


def test_actions_are_unique():
    rows = {tuple(row) for row in ACTION_TABLE}
    assert len(rows) == len(ACTIONS)


def test_neutral_action_presses_no_buttons():
    assert ACTION_TABLE[0].sum() == 0


def test_every_non_neutral_action_fires():
    for row in ACTION_TABLE[1:]:
        assert row[_B] == 1
