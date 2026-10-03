import numpy as np

NUM_NES_BUTTONS = 9
_B, _UNUSED, _SELECT, _START, _UP, _DOWN, _LEFT, _RIGHT, _A = range(NUM_NES_BUTTONS)
FRAMES_PER_DECISION = 4

HELD_ACTIONS = {
    "up": ((_UP,), "hold up"),
    "down": ((_DOWN,), "hold down"),
    "left": ((_LEFT,), "hold left"),
    "right": ((_RIGHT,), "hold right"),
}
TAPPED_ACTIONS = {
    "b": ((_B,), "press B"),
    "a": ((_A,), "press A"),
}

ACTION_DESCRIPTIONS = {name: description for name, (_, description) in {**HELD_ACTIONS, **TAPPED_ACTIONS}.items()}


def action_table() -> np.ndarray:
    table = np.zeros((len(ACTION_DESCRIPTIONS), FRAMES_PER_DECISION, NUM_NES_BUTTONS), dtype=np.int8)
    for index, (buttons, _) in enumerate(HELD_ACTIONS.values()):
        table[index, :, buttons] = 1
    for index, (buttons, _) in enumerate(TAPPED_ACTIONS.values(), start=len(HELD_ACTIONS)):
        table[index, 0, buttons] = 1
    return table


ACTION_TABLE = action_table()
