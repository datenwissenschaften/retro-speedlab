import numpy as np
import pytest

from src.ram.airstriker import AirstrikerRam
from src.states.survive import SurviveAndScore
from tests._helpers import encode_genesis_uint, encode_genesis_word

_FRAME = np.zeros((96, 96, 3), dtype=np.uint8)


def _ram(score: int = 0, lives: int = 3, game_over: bool = False) -> AirstrikerRam:
    return AirstrikerRam(
        score_bytes=encode_genesis_uint(score, 4),
        lives_bytes=encode_genesis_word(lives),
        game_over_bytes=encode_genesis_word(1 if game_over else 0),
    )


@pytest.fixture
def state() -> SurviveAndScore:
    instance = SurviveAndScore()
    instance.reset(_ram(score=0, lives=3), _FRAME, _FRAME)
    return instance


def test_survival_reward_with_no_change(state):
    reward, terminated, truncated, _ = state.step(_ram(score=0, lives=3), _FRAME, _FRAME)
    assert reward == pytest.approx(SurviveAndScore.survival_reward)
    assert terminated is False
    assert truncated is False


def test_reward_includes_score_gain(state):
    reward, *_ = state.step(_ram(score=50, lives=3), _FRAME, _FRAME)
    assert reward == pytest.approx(50 + SurviveAndScore.survival_reward)


def test_losing_a_life_penalizes_and_terminates(state):
    reward, terminated, _, _ = state.step(_ram(score=0, lives=2), _FRAME, _FRAME)
    expected = SurviveAndScore.survival_reward - SurviveAndScore.lost_life_penalty
    assert reward == pytest.approx(expected)
    assert terminated is True


def test_game_over_adds_the_game_over_penalty():
    instance = SurviveAndScore()
    instance.reset(_ram(score=0, lives=1), _FRAME, _FRAME)
    reward, terminated, _, _ = instance.step(_ram(score=0, lives=0, game_over=True), _FRAME, _FRAME)
    expected = SurviveAndScore.survival_reward - SurviveAndScore.lost_life_penalty - SurviveAndScore.game_over_penalty
    assert reward == pytest.approx(expected)
    assert terminated is True


def test_won_when_score_reaches_threshold():
    instance = SurviveAndScore()
    instance.reset(_ram(score=1_000, lives=3), _FRAME, _FRAME)
    assert instance._won() is True


def test_truncates_after_the_max_episode_steps(state):
    state.maximum_episode_steps = 3
    for _ in range(2):
        _, _, truncated, _ = state.step(_ram(score=0, lives=3), _FRAME, _FRAME)
        assert truncated is False
    _, _, truncated, _ = state.step(_ram(score=0, lives=3), _FRAME, _FRAME)
    assert truncated is True
