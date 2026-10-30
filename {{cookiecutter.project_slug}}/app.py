from pathlib import Path

from datenwissenschaften.workflow.lab import lab
from datenwissenschaften.workflow.launch import launch
from datenwissenschaften.workflow.speedrun import speedrun

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"
WRAPPER = "src.game.wrapper:GameWrapper"

__all__ = ["lab", "speedrun"]


def main() -> None:
    launch(speedrun, WRAPPER, CONFIG_PATH)


if __name__ == "__main__":
    main()
