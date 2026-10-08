from pathlib import Path

from datenwissenschaften.probe.run import probe

from src.game.wrapper import GameWrapper

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"
DECISIONS_PER_SEED = 300
SEED = 0


def main() -> None:
    probe(GameWrapper, CONFIG_PATH, DECISIONS_PER_SEED, SEED)


if __name__ == "__main__":
    main()
