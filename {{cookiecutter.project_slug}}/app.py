#!/usr/bin/env python3

from datenwissenschaften import EnvironmentBuilder, ModelBuilder, Trainer
from datenwissenschaften.recurrent_rnd import RecurrentRNDModel

from src.game.wrapper import AirstrikerWrapper


def main() -> None:
    config_path = "config.yaml"

    venv = EnvironmentBuilder(
        AirstrikerWrapper,
        render_mode="human",
        config_path=config_path,
    ).build()
    model = ModelBuilder(RecurrentRNDModel, config_path=config_path).build(venv)
    Trainer(config_path=config_path).train(model)


if __name__ == "__main__":
    main()
