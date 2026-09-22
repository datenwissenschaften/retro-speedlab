"""Byte-encoding helpers shared by RAM decoder tests.

These build word-swapped Genesis RAM byte sequences, the inverse of
``src.ram.airstriker.genesis_uint``, so tests can construct fixtures for
arbitrary score/lives values without an emulator.
"""


def encode_genesis_word(value: int) -> list[int]:
    """Encode a single 16-bit value into two word-swapped RAM bytes."""
    return [value & 0xFF, (value >> 8) & 0xFF]


def encode_genesis_uint(value: int, byte_length: int) -> list[int]:
    """Encode ``value`` into ``byte_length`` word-swapped RAM bytes."""
    if byte_length % 2:
        raise ValueError("byte_length must be even.")

    num_words = byte_length // 2
    words = []
    remaining = value
    for _ in range(num_words):
        words.append(remaining & 0xFFFF)
        remaining >>= 16
    words.reverse()

    raw: list[int] = []
    for word in words:
        raw.extend(encode_genesis_word(word))
    return raw
