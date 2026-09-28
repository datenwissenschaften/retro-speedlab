# {{ cookiecutter.project_name }}

{{ cookiecutter.description }}

This generated project is a complete Retro Speedlab example for
`Airstriker-Genesis-v0`. It uses Stable Retro, Gymnasium, the
`datenwissenschaften` state-machine environment, and the Laya decision model:
Laya reads the game's RAM as text, answers the current state's question with a
probability for every action, and learns from rewards.

## Quick start

Before starting training:

1. Use a GPU with at least 6 GB of memory. The first start downloads the Laya
   checkpoint configured under `laya.checkpoint`.
2. To submit runs and compete, create an account at
   <https://speedlab.datenwissenschaften.com/> and obtain an API key. Set that
   key as `upload.api_key` in `config.yaml`. You can leave the value set to
   `null` for local-only training.

Then install the project and start training:

```bash
poetry install
poetry run python app.py
```

Training metrics and controls are available at <http://127.0.0.1:18080> while
the process is running. <http://127.0.0.1:18080/stream> is a 1920×1080 stream
view for OBS that replays every frame with Laya's decision behind it.

## Included example game

Airstriker is the redistributable demo game included with Stable Retro. Its
`Level1` state and integration data are installed with the `stable-retro`
dependency, so this example runs without adding a commercial ROM. The `roms/`
directory remains available when replacing Airstriker with another legally
obtained game.

## Configuration

Edit `config.yaml` to control the game, savestate, Laya checkpoint, output
directories, the JSON training database, upload credentials, and local UI. All paths are relative
to the project directory.

Do not commit API keys. Keep `upload.api_key` set to `null` unless you intend to
upload competition runs, and keep credential-bearing configuration out of
version control.

## Example design

- `app.py` starts `LayaTrainer` with the Airstriker wrapper.
- `src/game/actions.py` defines three described actions (fire, left, right) as
  four-frame button sequences that tap fire once per decision.
- `src/game/wrapper.py` registers the states, RAM layout, and actions.
- `src/ram/airstriker.py` decodes score, lives, game-over state, and the ship's
  position, and describes them to Laya as readable text.
- `src/states/survive.py` rewards score and survival, penalizes lost lives, and
  bounds episode duration.
- `config.yaml` contains portable paths and reproducible training settings.

To adapt the generated project to another game, replace the action mapping,
RAM offsets, and state/reward logic, then update `training.game` and
`training.savestate`.

## Quality checks

```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest
```

`tests/` covers the action table, RAM decoding, and reward/termination logic
in `src/states/survive.py` without an emulator. It does not exercise
`app.py` itself, which requires Stable Retro's emulator core and a GPU for
Laya.

## License

{{ cookiecutter.license }}
