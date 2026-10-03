import numpy as np
from datenwissenschaften.states.landmarks import Landmarks

from src.game.actions import ACTION_DESCRIPTIONS, ACTION_TABLE, FRAMES_PER_DECISION, NUM_NES_BUTTONS
from src.game.wrapper import GameWrapper
from src.ram.game import GameRam
from src.states.play import FRAMES_PER_ATTEMPT, Play

FRAME = np.zeros((224, 240, 3), np.uint8)
EMPTY_RAM = bytes(0x800)


def test_the_skeleton_knows_nothing_about_the_game_yet() -> None:
    ram = GameRam.from_ram(EMPTY_RAM)

    assert GameWrapper.state_classes == (Play,)
    assert ACTION_TABLE.shape == (len(ACTION_DESCRIPTIONS), FRAMES_PER_DECISION, NUM_NES_BUTTONS)
    assert ram.describe() == {}


def test_attempts_are_only_time_limited(tmp_path) -> None:
    state = Play(Landmarks(tmp_path / "landmarks.json"))
    state.reset(GameRam.from_ram(EMPTY_RAM), FRAME)

    rewards, ended = [], False
    for _ in range(FRAMES_PER_ATTEMPT):
        reward, terminated, truncated, _ = state.step(GameRam.from_ram(EMPTY_RAM), FRAME)
        rewards.append(reward)
        ended = ended or terminated

    assert (set(rewards), ended, truncated) == ({0.0}, False, True)
