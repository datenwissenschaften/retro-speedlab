# {{ cookiecutter.project_name }}

The fastest run of {{ cookiecutter.game_title }} (`{{ cookiecutter.game }}`), searched frame by frame from power-on
by the [Retro Speedlab Core](https://github.com/datenwissenschaften/retro-speedlab-core) engine's speedrun search.
The search runs around the clock on the server as a Dokku app. When it is stuck in a segment, or the movie has not
improved for `agent.stall_minutes` minutes (the Flyte task `lab`, checked every `agent.schedule`), Claude Code works
on this package in a one-off container of that app (`agent/daily.sh`, prompt in `agent/PROMPT.md`): it measures,
changes the game package in `src/`, tests and commits it, and its branch ships only when the current movie still
replays. It follows the skill in `.claude/skills/beat-nes-game/SKILL.md` and writes a report per run into
`agent/reports/`. Every five reports, the critic (`agent/critic.sh`, `agent/CRITIC.md`) distils lessons into
`agent/LESSONS.md`.

The game package holds only game knowledge: the verified RAM map (`src/ram/game.py`), the actions
(`src/game/actions.py`), and the states of one run from power-on (`src/states/`), each with its goal, transitions
and rewards, grouped into levels in `src/game/wrapper.py`. The search beats each level on its own from a savestate
at its start (`working/cache/tas/levels.msgpack`), then builds the full run from power-on. It splits the movie at the
states' transitions.

This package starts as a skeleton that knows nothing about the game: the plain NES buttons, an empty `GameRam` and
one `Play` state without reward. The lab runs grow it from what they verify in the emulator.

## Quick start

The engine is a sibling checkout: clone
[retro-speedlab-core](https://github.com/datenwissenschaften/retro-speedlab-core) next to this project as
`../retro-speedlab-core`.

Copy `config.example.yaml` to `config.yaml`, fill in the `speedrun` section (speedrun.com and TASVideos ids of the
game and category) and set `upload.api_key` to relay the stream. `config.yaml` is ignored by git; never commit it.

Put the ROM you own as `roms/{{ cookiecutter.game }}.nes` into `roms/`; never commit it. A game Stable Retro does not
integrate gets its integration in `integrations/{{ cookiecutter.game }}/`. Then run:

    poetry install
    poetry run python app.py

Check that a movie still replays with the package:

    PYTHONPATH=. python -m datenwissenschaften.tas.run verify src.game.wrapper:GameWrapper config.yaml <progress.msgpack>

With `upload.api_key` set, the search relays its live stream to the backend at `upload.url`; the website plays it at
`https://www.retrospeedlab.com/stream?api_key=<stream key>`.

## Running on Dokku

The search runs as the Dokku app `dokku.app` on the server `dokku.host` (an SSH alias for the server's Dokku user).

Once, create and configure the app (no web proxy, no overlapping deploys). All persistent data lives on the server
under `dokku.data_dir`: `working/` holds the search's movie, progress and log. The directories are created through
your own login on the server with `sudo`:

    dokku/setup.sh

Clone this project and the engine into `dokku.workspace_dir` on the server; the lab runs work there. Every deploy
builds a repository from this project plus the committed `../retro-speedlab-core` and pushes it; commit core changes
first:

    dokku/deploy.sh

Follow the search and open the stream:

    ssh <dokku.host> logs <dokku.app> --tail
    https://www.retrospeedlab.com/stream?api_key=<stream key>

## Quality checks

    poetry run ruff check .
    poetry run ruff format --check .
    poetry run pytest

## License

GPL-3.0-only
