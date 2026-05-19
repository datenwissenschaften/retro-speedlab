# Retro Speedlab Cookiecutter

Start a retro reinforcement-learning project without rebuilding the boring parts.

This Cookiecutter template gives you a ready-to-hack training workspace with [stable-retro](https://stable-retro.farama.org/), a Gymnasium wrapper, a Stable-Baselines3 PPO model factory, Black/Ruff configuration, and project metadata wired through `pyproject.toml`.

## Why Use This Template?

Retro game experiments usually begin with the same setup work: environment wrappers, observation resizing, model defaults, Python metadata, formatting tools, and a repeatable run command. This template packages those decisions so contributors can spend their time on the interesting parts:

- shaping rewards for a specific game
- reading RAM values and game state
- experimenting with model architecture and hyperparameters
- sharing reproducible training projects with the community

The generated project is intentionally small. It is meant to be forked, modified, and argued with.

## Create A Project

Install Cookiecutter if you do not already have it:

```bash
pipx install cookiecutter
```

Generate a new project from this repository:

```bash
cookiecutter https://github.com/datenwissenschaften/retro-speedlab
```

Cookiecutter will ask for values such as the project name, description, author, license, and Python target. Those answers are rendered into the generated `pyproject.toml`.

## Generated Project

Your new project will include:

- `app.py` as the training entry point
- `.env.example` with the expected local runtime settings (including the API key from [speedlab.datenwissenschaften.com](https://speedlab.datenwissenschaften.com))
- `game/` for the Gymnasium wrapper and game-specific reward logic
- `model/` for the Stable-Baselines3 model builder
- `pyproject.toml` with Cookiecutter-rendered project metadata
- `.pre-commit-config.yaml` with formatting and basic quality hooks

Run the generated project from its own directory. Create a local environment file and install the dependencies:

```bash
cp .env.example .env
poetry install
poetry run python app.py
```

Or use your preferred virtual environment manager with the dependencies listed in `pyproject.toml`.

## ROMs

Generated projects use [stable-retro](https://stable-retro.farama.org/) to interface with classic games. Users must provide their own legally obtained ROMs to run experiments.

- Refer to the [stable-retro documentation](https://stable-retro.farama.org/getting_started/#importing-roms) to learn how to get your ROMs working.
- We do not favor piracy; only do what is correct by law.

## Template Variables

The main prompts are:

- `project_name`: human-readable project name
- `project_slug`: package/distribution slug used by `pyproject.toml`
- `version`: initial project version
- `description`: project summary
- `author_name` and `author_email`: rendered into `[project].authors`
- `license`: SPDX license expression
- `python_requires`: Python version range
- `python_classifier`: Python classifier version
- `python_target`: Black/Ruff target such as `py312`
- `development_status`: PyPI development-status classifier suffix

## Community Workflow

Good retro-agent projects are easier to learn from when the game-specific decisions are visible. When you publish a project generated from this template, consider documenting:

- the ROM/game version you trained against
- important RAM addresses and why they matter
- reward terms and termination conditions
- model changes from the default PPO setup
- videos or score curves from notable runs

Small, readable experiments are useful. Failed runs with clear notes are useful too.

## License

Generated projects default to `GPL-3.0-only`, but you can choose a different SPDX expression during generation.
