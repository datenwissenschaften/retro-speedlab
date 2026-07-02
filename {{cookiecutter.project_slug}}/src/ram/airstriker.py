from dataclasses import dataclass

from datenwissenschaften.ram import RamInfo, ram_array


def genesis_uint(raw_bytes: list[int]) -> int:
    """Decode a big-endian Genesis value from Stable Retro's word-swapped RAM."""
    if len(raw_bytes) % 2:
        raise ValueError("Genesis values must contain complete 16-bit words.")

    ordered = bytearray()
    for index in range(0, len(raw_bytes), 2):
        ordered.extend((raw_bytes[index + 1], raw_bytes[index]))
    return int.from_bytes(ordered, byteorder="big")


@dataclass(frozen=True)
class AirstrikerRam(RamInfo):
    # These offsets correspond to Stable Retro's Airstriker data.json. Genesis
    # RAM starts at 0xFF0000, so data address 0xFF024E maps to offset 0x024E.
    score_bytes: list[int] = ram_array(0x024E, 4)
    lives_bytes: list[int] = ram_array(0x025A, 2)
    game_over_bytes: list[int] = ram_array(0x0266, 2)

    @property
    def score(self) -> int:
        return genesis_uint(self.score_bytes)

    @property
    def lives(self) -> int:
        return genesis_uint(self.lives_bytes)

    @property
    def game_over(self) -> bool:
        return genesis_uint(self.game_over_bytes) == 1 and self.lives == 0
