import numpy as np

NUM_NES_BUTTONS = 9
_B, _UNUSED, _SELECT, _START, _UP, _DOWN, _LEFT, _RIGHT, _A = range(NUM_NES_BUTTONS)
FRAMES_PER_DECISION = 4

HELD_ACTIONS = {"up": _UP, "down": _DOWN, "left": _LEFT, "right": _RIGHT}
TAPPED_ACTIONS = {"b": _B, "a": _A, "start": _START}
ACTION_NAMES = [*HELD_ACTIONS, *TAPPED_ACTIONS]


def action_table() -> np.ndarray:
    table = np.zeros((len(ACTION_NAMES), FRAMES_PER_DECISION, NUM_NES_BUTTONS), dtype=np.int8)
    for index, button in enumerate(HELD_ACTIONS.values()):
        table[index, :, button] = 1
    for index, button in enumerate(TAPPED_ACTIONS.values(), start=len(HELD_ACTIONS)):
        table[index, 0, button] = 1
    return table


ACTION_TABLE = action_table()
