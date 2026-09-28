import argparse
import json
import random
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
import stable_retro
from loguru import logger

BYTE_RANGE = 256
HALF_BYTE_RANGE = 128
DIRECTIONS = ("UP", "DOWN", "LEFT", "RIGHT")
AXES = {"x": ("LEFT", "RIGHT"), "y": ("UP", "DOWN")}
BASE_COUNT = 8
BASE_SPACING_FRAMES = 240
HOLD_FRAMES = 24
IDLE_FRAMES = 1800
MIN_TIMER_TICKS = 3
MIN_TIMER_PERIOD_FRAMES = 8
MAX_TIMER_IRREGULARITY = 0.25
MAX_EVENT_CHANGES = 12
PLAY_SEGMENT_FRAMES = 1800
STACK_AND_SPRITE_PAGES = range(0x100, 0x300)
SCREENSHOT_KINDS = ("flag", "counter up", "counter down")
DIFFERENCE_ANCHORS = 5
DIFFERENCE_MARGIN_PIXELS = 3.0
SAMPLE_EVERY_FRAMES = 8
MAX_SAMPLES = 600
MIN_SPRITE_PIXELS = 20
MAX_SPRITE_PIXELS = 600
TOP_CANDIDATES = 6
PERCENTILES = (50, 90)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover the RAM values a Laya game package needs.")
    parser.add_argument("--game", required=True)
    parser.add_argument("--state", required=True)
    parser.add_argument("--play-minutes", type=float, required=True, help="random play for the event log")
    parser.add_argument("--playfield-bottom", type=int, required=True, help="first HUD row, excluded from sprites")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


class Emulator:
    def __init__(self, game: str, state: str, seed: int) -> None:
        self.env = stable_retro.make(game, state=state, render_mode=None)
        self.env.reset(seed=seed)
        self.buttons = list(self.env.buttons)
        self.game_path = Path(stable_retro.data.get_file_path(game, "data.json"))

    def press(self, names: tuple[str, ...]) -> np.ndarray:
        buttons = np.zeros(len(self.buttons), dtype=np.int8)
        for name in names:
            buttons[self.buttons.index(name)] = 1
        frame, *_ = self.env.step(buttons)
        return frame

    def ram(self) -> np.ndarray:
        return self.env.get_ram().astype(np.int64)

    def save(self) -> bytes:
        return self.env.em.get_state()

    def restore(self, emulator_state: bytes) -> None:
        self.env.em.set_state(emulator_state)
        self.env.data.reset()
        self.env.data.update_ram()


def signed_delta(after: np.ndarray, before: np.ndarray) -> np.ndarray:
    return (after - before + HALF_BYTE_RANGE) % BYTE_RANGE - HALF_BYTE_RANGE


def known_variables(emulator: Emulator) -> dict[str, object]:
    return json.loads(emulator.game_path.read_text())["info"]


def collect_bases(emulator: Emulator, rng: random.Random) -> list[bytes]:
    bases = [emulator.save()]
    directions = [name for name in DIRECTIONS if name in emulator.buttons]
    while len(bases) < BASE_COUNT:
        held = (rng.choice(directions),)
        for frame in range(BASE_SPACING_FRAMES):
            if frame % HOLD_FRAMES == 0:
                held = (rng.choice(directions),)
            emulator.press(held)
        bases.append(emulator.save())
    return bases


def input_response(emulator: Emulator, bases: list[bytes]) -> dict[str, np.ndarray]:
    responses = {}
    for direction in DIRECTIONS:
        deltas = []
        for base in bases:
            emulator.restore(base)
            before = emulator.ram()
            for _ in range(HOLD_FRAMES):
                emulator.press((direction,))
            deltas.append(signed_delta(emulator.ram(), before))
        responses[direction] = np.array(deltas)
    return responses


def position_candidates(responses: dict[str, np.ndarray]) -> dict[str, list[dict[str, object]]]:
    candidates = {}
    for axis, (negative, positive) in AXES.items():
        agreement = np.mean(np.sign(responses[positive]) - np.sign(responses[negative]), axis=0) / 2
        ranked = np.argsort(-np.abs(agreement))[:TOP_CANDIDATES]
        candidates[axis] = [
            {
                "address": hex(int(address)),
                "agreement": round(float(agreement[address]), 2),
                "response": {name: round(float(responses[name][:, address].mean()), 1) for name in DIRECTIONS},
            }
            for address in ranked
            if agreement[address] != 0
        ]
    return candidates


def timer_candidates(emulator: Emulator, start: bytes) -> list[dict[str, object]]:
    emulator.restore(start)
    history = []
    for _ in range(IDLE_FRAMES):
        emulator.press(())
        history.append(emulator.ram())
    values = np.array(history)
    timers = []
    for address in range(values.shape[1]):
        ticks = np.flatnonzero(np.diff(values[:, address]))
        if len(ticks) < MIN_TIMER_TICKS:
            continue
        steps = np.diff(values[:, address])[ticks]
        intervals = np.diff(ticks)
        if (
            np.mean(steps < 0) < 1 - MAX_TIMER_IRREGULARITY
            or intervals.std() > MAX_TIMER_IRREGULARITY * intervals.mean()
            or intervals.mean() < MIN_TIMER_PERIOD_FRAMES
        ):
            continue
        timers.append(
            {"address": hex(address), "frames_per_tick": float(intervals.mean()), "start": int(values[0, address])}
        )
    return timers


class EventLog:
    def __init__(self, out: Path) -> None:
        self.out = out
        self.changes: Counter[int] = Counter()
        self.transitions: dict[int, list[tuple[int, int]]] = {}
        self.first_frames: dict[int, np.ndarray] = {}
        self.samples: list[tuple[np.ndarray, np.ndarray]] = []

    def record(self, frame_index: int, frame: np.ndarray, before: np.ndarray, after: np.ndarray) -> None:
        for address in map(int, np.flatnonzero(before != after)):
            if address in STACK_AND_SPRITE_PAGES:
                continue
            self.changes[address] += 1
            if self.changes[address] > MAX_EVENT_CHANGES:
                continue
            self.transitions.setdefault(address, []).append((int(before[address]), int(after[address])))
            self.first_frames.setdefault(address, frame)
        if frame_index % SAMPLE_EVERY_FRAMES == 0 and len(self.samples) < MAX_SAMPLES:
            self.samples.append((frame, after))

    def rare_bytes(self) -> list[dict[str, object]]:
        rare = sorted(address for address, count in self.changes.items() if count <= MAX_EVENT_CHANGES)
        events = [
            {
                "address": hex(address),
                "kind": self._kind(self.transitions[address]),
                "changes": self.transitions[address],
            }
            for address in rare
        ]
        for address in rare:
            old, new = self.transitions[address][0]
            image = cv2.cvtColor(self.first_frames[address], cv2.COLOR_RGB2BGR)
            cv2.imwrite(str(self.out / f"{hex(address)}_{old}_to_{new}.png"), image)
        return sorted(
            events, key=lambda event: SCREENSHOT_KINDS.index(event["kind"]) if event["kind"] in SCREENSHOT_KINDS else 3
        )

    @staticmethod
    def _kind(changes: list[tuple[int, int]]) -> str:
        steps = [new - old for old, new in changes]
        if all(value in (0, 1) for change in changes for value in change):
            return "flag"
        if all(step == 1 for step in steps):
            return "counter up"
        if all(step == -1 for step in steps):
            return "counter down"
        return "rare value"


def play(emulator: Emulator, bases: list[bytes], seconds: float, rng: random.Random, log: EventLog) -> None:
    frames = int(seconds * 60)
    playable = [name for name in emulator.buttons if name not in (None, "START", "SELECT")]
    held: tuple[str, ...] = ()
    before = emulator.ram()
    for index in range(frames):
        if index % PLAY_SEGMENT_FRAMES == 0:
            emulator.restore(rng.choice(bases))
            before = emulator.ram()
        if index % HOLD_FRAMES == 0:
            held = tuple(rng.sample(playable, rng.randint(1, 2)))
        frame = emulator.press(held)
        after = emulator.ram()
        log.record(index, frame, before, after)
        before = after


def largest_blob_centers(frame: np.ndarray, color: tuple[int, ...], bottom: int) -> tuple[float, float] | None:
    mask = np.all(frame[:bottom] == color, axis=2).astype(np.uint8)
    count, _, stats, centroids = cv2.connectedComponentsWithStats(mask)
    if count < 2:
        return None
    largest = 1 + int(np.argmax(stats[1:, 4]))
    if not MIN_SPRITE_PIXELS <= stats[largest, 4] <= MAX_SPRITE_PIXELS:
        return None
    return float(centroids[largest][0]), float(centroids[largest][1])


def screen_fit(samples: list[tuple[np.ndarray, np.ndarray]], addresses: list[int], bottom: int) -> dict[str, dict]:
    frames = [frame for frame, _ in samples[:: max(1, len(samples) // 20)]]
    colors = {tuple(map(int, pixel)) for frame in frames for pixel in np.unique(frame[:bottom].reshape(-1, 3), axis=0)}
    best: dict[str, dict] = {"x": {"correlation": 0.0}, "y": {"correlation": 0.0}}
    for color in colors:
        pairs = [(largest_blob_centers(frame, color, bottom), ram) for frame, ram in samples]
        found = [(center, ram) for center, ram in pairs if center is not None]
        if len(found) < len(samples) // 4:
            continue
        centers = np.array([center for center, _ in found])
        rams = np.array([ram for _, ram in found])
        for axis_index, axis in enumerate(("x", "y")):
            for address in addresses:
                fit = linear_fit(rams[:, address], centers[:, axis_index])
                if fit["correlation"] > best[axis]["correlation"]:
                    best[axis] = {"address": hex(address), "color": list(color), **fit}
    return best


def player_formulas(samples: list[tuple[np.ndarray, np.ndarray]], color: list[int], bottom: int) -> dict:
    found = [(largest_blob_centers(frame, tuple(color), bottom), ram) for frame, ram in samples]
    centers = np.array([center for center, _ in found if center is not None])
    rams = np.array([ram for center, ram in found if center is not None])
    return {axis: best_formula(rams, centers[:, index]) for index, axis in enumerate(("x", "y"))}


def best_formula(rams: np.ndarray, target: np.ndarray) -> dict[str, object]:
    addresses = [address for address in range(rams.shape[1]) if address not in STACK_AND_SPRITE_PAGES]
    singles = {address: linear_fit(rams[:, address], target) for address in addresses}
    anchors = sorted(singles, key=lambda address: singles[address]["correlation"], reverse=True)[:DIFFERENCE_ANCHORS]
    differences = {}
    for anchor in anchors:
        for address in addresses:
            for first, second in ((address, anchor), (anchor, address)):
                values = (rams[:, first] - rams[:, second]) % BYTE_RANGE
                differences[f"(ram[{hex(first)}] - ram[{hex(second)}]) % 256"] = linear_fit(values, target)
    single_name, single = most_accurate({f"ram[{hex(address)}]": fit for address, fit in singles.items()})
    difference_name, difference = most_accurate(differences)
    clearly_better = difference["error_percentiles"][1] < single["error_percentiles"][1] - DIFFERENCE_MARGIN_PIXELS
    return {
        "formula": difference_name if clearly_better else single_name,
        "single": {"formula": single_name, **single},
        "difference": {"formula": difference_name, **difference},
    }


def most_accurate(formulas: dict[str, dict]) -> tuple[str, dict]:
    fitted = {name: fit for name, fit in formulas.items() if "error_percentiles" in fit}
    name = min(fitted, key=lambda formula: fitted[formula]["error_percentiles"][1])
    return name, fitted[name]


def linear_fit(values: np.ndarray, target: np.ndarray) -> dict[str, object]:
    if values.std() == 0:
        return {"correlation": 0.0}
    offset = float(np.median(target - values))
    errors = np.abs(target - values - offset)
    return {
        "correlation": round(float(abs(np.corrcoef(values, target)[0, 1])), 3),
        "screen_offset": round(offset, 1),
        "error_percentiles": [round(float(p), 1) for p in np.percentile(errors, PERCENTILES)],
    }


def main() -> None:
    arguments = parse_arguments()
    (arguments.out / "events").mkdir(parents=True, exist_ok=True)
    rng = random.Random(arguments.seed)
    emulator = Emulator(arguments.game, arguments.state, arguments.seed)
    start = emulator.save()
    bases = collect_bases(emulator, rng)
    positions = position_candidates(input_response(emulator, bases))
    log = EventLog(arguments.out / "events")
    play(emulator, bases, arguments.play_minutes * 60, rng, log)
    report = {
        "buttons": emulator.buttons,
        "known_variables": known_variables(emulator),
        "position": positions,
        "screen_fit": screen_fit(
            log.samples,
            [int(candidate["address"], 16) for axis in ("x", "y") for candidate in positions[axis]],
            arguments.playfield_bottom,
        ),
        "timers": timer_candidates(emulator, start),
        "events": log.rare_bytes(),
    }
    if "color" in report["screen_fit"]["x"]:
        report["player"] = {
            "color": report["screen_fit"]["x"]["color"],
            **player_formulas(log.samples, report["screen_fit"]["x"]["color"], arguments.playfield_bottom),
        }
    (arguments.out / "ram_map.json").write_text(json.dumps(report, indent=2))
    logger.info(f"RAM map written to {arguments.out / 'ram_map.json'} with {len(report['events'])} event bytes")


if __name__ == "__main__":
    main()
