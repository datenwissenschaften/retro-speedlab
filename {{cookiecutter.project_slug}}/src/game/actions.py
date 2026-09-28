import numpy as np

_NUM_GENESIS_BUTTONS = 12
(
    _B,
    _A,
    _MODE,
    _START,
    _UP,
    _DOWN,
    _LEFT,
    _RIGHT,
    _C,
    _Y,
    _X,
    _Z,
) = range(_NUM_GENESIS_BUTTONS)

FRAMES_PER_DECISION = 4

# Airstriker fires only when B goes from released to pressed, so every decision taps B once.
# Untrained Laya starts closest to balanced with the options in this order.
ACTIONS = (
    (_RIGHT,),
    (),
    (_LEFT,),
)

ACTION_DESCRIPTIONS = {
    "right": "dodge to the right while shooting",
    "fire": "hold position and shoot straight ahead",
    "left": "dodge to the left while shooting",
}


def action_table() -> np.ndarray:
    table = np.zeros((len(ACTIONS), FRAMES_PER_DECISION, _NUM_GENESIS_BUTTONS), dtype=np.int8)
    for index, buttons in enumerate(ACTIONS):
        table[index, :, buttons] = 1
        table[index, 0, _B] = 1
    return table


ACTION_TABLE = action_table()
