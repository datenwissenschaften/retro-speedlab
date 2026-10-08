# {{ cookiecutter.project_name }}

Laya learns to beat `{{ cookiecutter.game }}` by itself in the
[Retro Speedlab](https://www.retrospeedlab.com). This game package starts as a
skeleton that knows nothing about the game; scheduled Claude Code lab runs grow
it from what they verify in the emulator, and the
[Retro Speedlab Core](https://github.com/datenwissenschaften/retro-speedlab-core)
engine turns it into a learning agent.

## The skeleton

- `src/game/actions.py`: the plain NES buttons, held directions and tapped
  `A`/`B`, as four-frame button sequences
- `src/ram/game.py`: an empty `GameRam`, so Laya is told nothing yet
- `src/states/play.py`: one `Play` state with the question "Which move?", no
  reward, and attempts limited to 18,000 frames
- `src/game/wrapper.py`: the `StateMachineGymWrapper` that wires them together
- `tests/test_play.py`: pins down that the skeleton knows nothing yet

Every attempt boots the game at power-on, like a real speedrun. Everything else
(RAM map, the menu and level phases, detectors, hints, rewards and curriculum
seeds) is built by the lab runs, following
`.claude/skills/beat-nes-game/SKILL.md`.

## Quick start

1. Put the ROM Stable Retro expects for `{{ cookiecutter.game }}` into
   `roms/`. It is imported automatically when training starts; never commit
   it.
2. Use a GPU with at least 6 GB of memory. The first start downloads the Laya
   checkpoint configured under `laya.checkpoint`.
3. Install and train:

   ```bash
   poetry install
   poetry run python app.py
   ```

With `upload.api_key` set, the training relays its live stream to the Retro
Speedlab backend; the website's `/stream?api_key=<stream key>` page replays every
frame with Laya's decision behind it, for OBS.

## Configuration

`config.yaml` holds the game, the levels in training order, the Laya
checkpoint, output directories, the JSON training database, lab reports,
uploads, the local UI and the server deployment. All paths are relative to the
project directory.

Keep `upload.api_key` set to `null` for local-only training. With a key, every
level Laya beats from its first frame and every short lab report is uploaded to
the Retro Speedlab API under `upload.url`. Never commit a real key.

## Lab runs on a GPU server

Training runs around the clock in a [Dokku](https://dokku.com) app on a GPU
server, and four times a day (`agent.schedule`) Claude Code runs there
unattended in a one-off container of the same app (`agent/daily.sh`, prompt in
`agent/PROMPT.md`). Each lab run measures the progress, ships at least one
verified change to the game package, tests it, commits, deploys and writes a
lab report into `agent/reports/`. The permissions in `.claude/settings.json`
forbid `sudo`, pushing and editing the training data.

Every value the scripts need is in the `dokku` and `agent` sections of
`config.yaml`. Once:

```bash
dokku/setup.sh
ssh <dokku.host> config:set --no-restart <dokku.app> CLAUDE_CODE_OAUTH_TOKEN=<token from claude setup-token>
```

Clone this project into `dokku.workspace_dir` on the server, then deploy:

```bash
dokku/deploy.sh
```

Each deploy registers the lab run with Dokku's scheduler. Write server
specifics (training data folder, backend address) into `NOTES.md`; the lab
runs read them there.

## Quality checks

```bash
poetry run ruff check .
poetry run ruff format --check .
poetry run pytest
```

## License

GPL-3.0-only
