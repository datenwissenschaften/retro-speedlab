# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

This project trains a retro-game reinforcement-learning agent with [stable-retro](https://stable-retro.farama.org/), Gymnasium, and Stable-Baselines3. The starter layout keeps game logic, model construction, and the training entry point separate so experiments stay easy to change.

## Setup

Create a local environment file and install the dependencies:

```bash
cp .env.example .env
poetry install
```

## ROMs

This project requires game ROMs to function. You must provide your own legally obtained ROMs. 

- Place your ROMs in the `roms/` directory (or the path configured via `RETRO_SPEEDLAB_ROM_PATH`).
- For instructions on how to get ROMs working, refer to the [stable-retro documentation](https://stable-retro.farama.org/getting_started/#importing-roms).
- **Disclaimer:** We do not favor piracy. Please only use ROMs that you have the legal right to use according to your local laws.

## Run

Use the platform launcher (which also installs dependencies and initializes the environment):

- Linux/macOS: `./run.sh`
- Windows Command Prompt: `run.bat`
- Windows PowerShell: `.\run.ps1`
 
## Configuration

Configure your local environment by copying `.env.example` to `.env`. The following variables control the training process:

- `RETRO_SPEEDLAB_TIMESTEPS`: Total number of training timesteps.
- `RETRO_SPEEDLAB_NUM_ENVS`: Number of parallel environments for training.
- `RETRO_SPEEDLAB_GAME_ID`: stable-retro game ID (e.g., `SuperMarioWorld-Snes-v0`).
- `RETRO_SPEEDLAB_SAVESTATE`: Name of the savestate to start from.
- `RETRO_SPEEDLAB_MODEL_DIR`: Directory for saving models.
- `RETRO_SPEEDLAB_RECORDING_DIR`: Directory for saving training recordings.
- `RETRO_SPEEDLAB_ROM_PATH`: Path to the directory containing ROMs.
- `RETRO_SPEEDLAB_API_KEY`: API key for the Retro Speedlab platform (get yours at [speedlab.datenwissenschaften.com](https://speedlab.datenwissenschaften.com)).

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
