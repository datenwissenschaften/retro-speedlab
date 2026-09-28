from dataclasses import dataclass
from typing import Any

from datenwissenschaften.ram import RamInfo, ram_array

SHIP_LEFT_EDGE = 137
SHIP_RIGHT_EDGE = 412


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
    ship_x_bytes: list[int] = ram_array(0x0268, 2)

    @property
    def score(self) -> int:
        return genesis_uint(self.score_bytes)

    @property
    def lives(self) -> int:
        return genesis_uint(self.lives_bytes)

    @property
    def game_over(self) -> bool:
        return genesis_uint(self.game_over_bytes) == 1 and self.lives == 0

    @property
    def ship_position_percent(self) -> int:
        ship_x = genesis_uint(self.ship_x_bytes)
        return round((ship_x - SHIP_LEFT_EDGE) * 100 / (SHIP_RIGHT_EDGE - SHIP_LEFT_EDGE))

    def describe(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "lives": self.lives,
            "ship_position_percent_from_left": self.ship_position_percent,
        }
