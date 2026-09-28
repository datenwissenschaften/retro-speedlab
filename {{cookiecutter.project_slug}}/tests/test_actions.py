import numpy as np

from src.game.actions import (
    _B,
    _LEFT,
    _NUM_GENESIS_BUTTONS,
    _RIGHT,
    ACTION_DESCRIPTIONS,
    ACTION_TABLE,
    ACTIONS,
    FRAMES_PER_DECISION,
)


def test_action_table_is_a_button_sequence_per_action():
    assert ACTION_TABLE.shape == (len(ACTIONS), FRAMES_PER_DECISION, _NUM_GENESIS_BUTTONS)
    assert ACTION_TABLE.dtype == np.int8


def test_every_action_taps_fire_once_so_the_game_registers_a_new_shot():
    for frames in ACTION_TABLE:
        assert frames[:, _B].tolist() == [1] + [0] * (FRAMES_PER_DECISION - 1)


def test_movement_is_held_for_the_whole_decision():
    assert ACTION_TABLE[0, :, _RIGHT].tolist() == [1] * FRAMES_PER_DECISION
    assert ACTION_TABLE[1, :, [_LEFT, _RIGHT]].sum() == 0
    assert ACTION_TABLE[2, :, _LEFT].tolist() == [1] * FRAMES_PER_DECISION


def test_every_action_is_described_for_laya():
    assert len(ACTION_DESCRIPTIONS) == len(ACTIONS)
