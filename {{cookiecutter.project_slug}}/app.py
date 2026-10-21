from pathlib import Path

from datenwissenschaften.workflow.lab import lab
from datenwissenschaften.workflow.launch import run_training
from datenwissenschaften.workflow.training import training

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"
WRAPPER = "src.game.wrapper:GameWrapper"

__all__ = ["lab", "training"]


def main() -> None:
    run_training(WRAPPER, CONFIG_PATH)


if __name__ == "__main__":
    main()
