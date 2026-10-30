from src.game.actions import ACTION_NAMES, ACTION_TABLE, FRAMES_PER_DECISION, NUM_NES_BUTTONS
from src.game.wrapper import GameWrapper
from src.ram.game import GameRam
from src.states.play import Play

EMPTY_RAM = bytes(0x800)


def test_the_skeleton_knows_nothing_about_the_game_yet() -> None:
    ram = GameRam.from_ram(EMPTY_RAM)

    assert GameWrapper.state_classes == (Play,)
    assert GameWrapper.levels == ()
    assert ACTION_TABLE.shape == (len(ACTION_NAMES), FRAMES_PER_DECISION, NUM_NES_BUTTONS)
    assert ram.describe() == {}
    assert ram.position() is None
    assert ram.remaining_lives() is None
    assert ram.dynamics() == ()


def test_the_skeleton_pays_nothing_and_never_leaves_play() -> None:
    state = Play()
    state.reset(GameRam.from_ram(EMPTY_RAM))

    assert state.step(GameRam.from_ram(EMPTY_RAM)) == (0.0, False, False, None)
