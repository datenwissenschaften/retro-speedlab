import gymnasium as gym
import numpy as np

_NUM_GENESIS_BUTTONS = 12
_B, _A, _MODE, _START, _UP, _DOWN, _LEFT, _RIGHT, _C, _Y, _X, _Z = range(_NUM_GENESIS_BUTTONS)

# Airstriker only needs movement and one fire button. Shooting is combined with
# movement because there is no gameplay reason to stop firing during a run.
ACTIONS = (
    (),
    (_B,),
    (_UP, _B),
    (_DOWN, _B),
    (_LEFT, _B),
    (_RIGHT, _B),
    (_UP, _LEFT, _B),
    (_UP, _RIGHT, _B),
    (_DOWN, _LEFT, _B),
    (_DOWN, _RIGHT, _B),
)


def action_table() -> np.ndarray:
    table = np.zeros((len(ACTIONS), _NUM_GENESIS_BUTTONS), dtype=np.int8)
    for index, buttons in enumerate(ACTIONS):
        table[index, buttons] = 1
    return table


ACTION_TABLE = action_table()