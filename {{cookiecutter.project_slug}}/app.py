from pathlib import Path

from datenwissenschaften.training.trainer import LayaTrainer

from src.game.wrapper import GameWrapper

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


def main() -> None:
    LayaTrainer(GameWrapper, CONFIG_PATH).train()


if __name__ == "__main__":
    main()
