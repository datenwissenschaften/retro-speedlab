from datenwissenschaften.states.state import State

from src.ram.game import GameRam


class Play(State[GameRam]):
    description = "Which move?"
