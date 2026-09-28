#!/usr/bin/env python3

from pathlib import Path

from datenwissenschaften.training.trainer import LayaTrainer

from src.game.wrapper import AirstrikerWrapper

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


def main() -> None:
    LayaTrainer(AirstrikerWrapper, CONFIG_PATH).train()


if __name__ == "__main__":
    main()
