from datenwissenschaften.states.state import State

from src.ram.game import GameRam

FRAMES_PER_ATTEMPT = 18_000


class Play(State[GameRam]):
    description = "Which move?"
    frames: int

    def _on_reset(self) -> None:
        self.frames = 0

    def _reward(self) -> float:
        self.frames += 1
        return 0.0

    def _truncated(self) -> bool:
        return self.frames >= FRAMES_PER_ATTEMPT
