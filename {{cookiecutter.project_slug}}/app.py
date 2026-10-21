from pathlib import Path

import flyte
from datenwissenschaften.workflow.lab import lab
from datenwissenschaften.workflow.training import training

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"
WRAPPER = "src.game.wrapper:GameWrapper"

__all__ = ["lab", "training"]


def main() -> None:
    flyte.init()
    flyte.run(training, wrapper=WRAPPER, config=str(CONFIG_PATH))


if __name__ == "__main__":
    main()
