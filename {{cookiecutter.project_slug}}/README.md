# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

This project trains a retro-game reinforcement-learning agent with Gymnasium and Stable-Baselines3. The starter layout keeps game logic, model construction, and the training entry point separate so experiments stay easy to change.

## Setup

Create a local environment file and install the dependencies:

```bash
cp .env.example .env
poetry install
```

## Run

Use the platform launcher (which also installs dependencies and initializes the environment):

- Linux/macOS: `./run.sh`
- Windows Command Prompt: `run.bat`
- Windows PowerShell: `.\run.ps1`
 
## Configuration

Configure your local environment by copying `.env.example` to `.env`. The following variables control the training process:

- `RETRO_ARENA_TIMESTEPS`: Total number of training timesteps.
- `RETRO_ARENA_NUM_ENVS`: Number of parallel environments for training.
- `RETRO_ARENA_GAME_ID`: Gymnasium-Retro game ID (e.g., `SuperMarioWorld-Snes-v0`).
- `RETRO_ARENA_SAVESTATE`: Name of the savestate to start from.
- `RETRO_ARENA_MODEL_DIR`: Directory for saving models.
- `RETRO_ARENA_RECORDING_DIR`: Directory for saving training recordings.
- `RETRO_ARENA_ROM_PATH`: Path to the directory containing ROMs.
- `RETRO_ARENA_API_KEY`: API key for the Retro Arena platform (get yours at [arena.datenwissenschaften.com](https://arena.datenwissenschaften.com)).

## Project Layout

- `app.py`: starts the training run
- `run.sh`, `run.bat`, `run.ps1`: platform launchers
- `.env.example`: documents the local runtime variables
- `game/`: Gymnasium wrapper, observation processing, rewards, and termination logic
- `model/`: PPO model configuration and learning-rate schedule
- `pyproject.toml`: project metadata, dependencies, and formatter/linter settings

## What To Customize

- Update RAM addresses and reward logic in `game/__init__.py`.
- Tune PPO settings in `model/__init__.py`.
- Configure the environment variables in `.env` as described in the **Configuration** section.
- Record assumptions about the ROM, savestates, and scoring rules here so other contributors can reproduce your runs.

## License

{{ cookiecutter.license }}
