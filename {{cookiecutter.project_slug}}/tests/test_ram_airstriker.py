import pytest

from src.ram.airstriker import AirstrikerRam, genesis_uint
from tests._helpers import encode_genesis_uint, encode_genesis_word


def test_genesis_uint_swaps_a_single_word():
    # A single 16-bit word is byte-swapped, then read big-endian.
    assert genesis_uint([0x34, 0x12]) == 0x1234


def test_genesis_uint_rejects_odd_length():
    with pytest.raises(ValueError):
        genesis_uint([0x00])


@pytest.mark.parametrize("value", [0, 1, 255, 1000, 65_535, 123_456, 2**31 - 1])
def test_genesis_uint_round_trips_through_encoder(value):
    byte_length = 4 if value > 0xFFFF else 2
    assert genesis_uint(encode_genesis_uint(value, byte_length)) == value


def test_airstriker_ram_reads_score_lives_and_game_over():
    ram = AirstrikerRam(
        score_bytes=encode_genesis_uint(1_280, 4),
        lives_bytes=encode_genesis_word(2),
        game_over_bytes=encode_genesis_word(0),
    )
    assert ram.score == 1_280
    assert ram.lives == 2
    assert ram.game_over is False


def test_airstriker_ram_game_over_requires_zero_lives():
    ram = AirstrikerRam(
        score_bytes=encode_genesis_uint(0, 4),
        lives_bytes=encode_genesis_word(1),
        game_over_bytes=encode_genesis_word(1),
    )
    # The game-over flag alone is not enough; lives must also be zero.
    assert ram.game_over is False

    ram_out_of_lives = AirstrikerRam(
        score_bytes=encode_genesis_uint(0, 4),
        lives_bytes=encode_genesis_word(0),
        game_over_bytes=encode_genesis_word(1),
    )
    assert ram_out_of_lives.game_over is True
