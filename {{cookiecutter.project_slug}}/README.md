# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

This generated project is a complete Retro Speedlab example for
`Airstriker-Genesis-v0`. It uses Stable Retro, Gymnasium, the
`datenwissenschaften` state-machine environment, and recurrent PPO with random
network distillation (RND).

## Quick start

```bash
poetry install
poetry run python app.py
```

Training metrics and controls are available at <http://127.0.0.1:18080> while
the process is running.

## Included example game

Airstriker is the redistributable demo game included with Stable Retro. Its
`Level1` state and integration data are installed with the `stable-retro`
dependency, so this example runs without adding a commercial ROM. The `roms/`
directory remains available when replacing Airstriker with another legally
obtained game.

## Configuration

Edit `config.yaml` to control the game, savestate, training budget, parallel
environment count, output directories, upload credentials, and local UI. All
paths are relative to the project directory.

Do not commit API keys. Leave `upload.api_key` set to `null` unless uploads are
required, and keep any credential-bearing configuration out of version control.

## Example design

- `app.py` wires the environment, recurrent RND model, and trainer together.
- `src/game/actions.py` reduces the 12-button Genesis controller to ten useful
  movement-and-fire actions.
- `src/game/wrapper.py` turns those discrete actions into emulator button
  vectors and emits 96×96 visual plus RAM observations.
- `src/ram/airstriker.py` decodes score, lives, and game-over state from the
  bundled Stable Retro integration.
- `src/states/survive.py` rewards score and survival, penalizes lost lives, and
  bounds episode duration.
- `config.yaml` contains portable paths and reproducible training settings.

To adapt the generated project to another game, replace the action mapping,
RAM offsets, and state/reward logic, then update `training.game` and
`training.savestate`.

## Quality checks

```bash
poetry run ruff check .
poetry run black --check .
```

## License

{{ cookiecutter.license }}
