#!/usr/bin/env python3
import os
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    """Launcher or training entry point."""
    if sys.prefix != sys.base_prefix or os.environ.get("POETRY_ACTIVE") == "1":
        # In a virtual environment, run the training
        from dotenv import load_dotenv
        from datenwissenschaften import EnvironmentBuilder, ModelBuilder, Trainer

        from game import GymWrapper
        from model import ModelWrapper

        load_dotenv()
        venv = EnvironmentBuilder(GymWrapper).build()
        model = ModelBuilder(ModelWrapper).build(venv)
        Trainer().train(model)
    else:
        # Not in a virtual environment, try to use poetry
        if shutil.which("poetry") is None:
            print("Poetry is required. Install it, then run: poetry install", file=sys.stderr)
            sys.exit(127)

        project_dir = Path(__file__).resolve().parent
        subprocess.run(["poetry", "install"], cwd=project_dir, check=True)
        sys.exit(
            subprocess.run(
                ["poetry", "run", "python", __file__],
                cwd=project_dir,
                check=False,
            ).returncode
        )


if __name__ == "__main__":
    main()
