#!/usr/bin/env python3

import argparse
from functools import partial
from pathlib import Path

from datenwissenschaften import EnvironmentBuilder, ModelBuilder, StateTrainer
from datenwissenschaften.rnd import AdaptiveRecurrentRNDModel

from src.game.wrapper import AirstrikerWrapper


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path, nargs="?", default=Path("config.yaml"))
    args = parser.parse_args()

    wrapper = partial(AirstrikerWrapper, config_path=args.config)
    venv = EnvironmentBuilder(
        wrapper,
        render_mode="rgb_array",
        config_path=args.config,
    ).build()
    StateTrainer(
        ModelBuilder(AdaptiveRecurrentRNDModel, config_path=args.config),
        transition_bonus=0.0,
        config_path=args.config,
    ).train(venv)


if __name__ == "__main__":
    main()
