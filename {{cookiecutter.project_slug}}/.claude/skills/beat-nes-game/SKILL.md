---
name: beat-nes-game
description: Turn this generated retro-speedlab project into a game package (automatic RAM discovery), train, diagnose and regularly optimize a retro-speedlab game package that beats an NES level with Laya (one Laya model per state machine state). Use when creating a new game package, when a game's training stalls or collapses, when asked to review rewards, detections or curriculum progress, or on a scheduled optimization run for a game project.
---

# Beat an NES game with Laya

This project was generated from the retro-speedlab template and still contains its Airstriker example. It
depends on `retro-speedlab-core` (the engine, `datenwissenschaften` on PyPI,
https://github.com/datenwissenschaften/retro-speedlab-core) and contains only game knowledge: RAM map,
detectors, actions, states, rewards. The engine owns learning, curriculum, UI and deployment. Work in small
verified steps, follow the engine's `AGENTS.md` (no defaults, fail fast, ruff, loguru, python-box, no
comments), and record every verified game fact in `NOTES.md`.

Run every command from the project root. Placeholders used below:

| Placeholder | Meaning |
|---|---|
| `<Game>-Nes-v0` | the stable-retro game id, for example `SuperMarioBros-Nes-v0` |
| `<state>` | a start savestate of that game, for example `Level1-1` |
| `<game>` | a short module name for the game, for example `super_mario_bros` |

## 1. Turn the template into the game package

1. **Install and import the ROM** (the user supplies a ROM they own, placed in `roms/`, which git ignores):
   ```bash
   poetry install
   poetry run python -m stable_retro.import roms
   poetry run python -c "import stable_retro, pathlib; print(pathlib.Path(stable_retro.data.get_file_path('<Game>-Nes-v0', 'data.json')).parent)"
   ```
   That directory holds `data.json` (known RAM variables), `scenario.json` (done condition) and `*.state`
   (start states). 298 NES games are integrated; a missing game needs a stable-retro integration first.
   To develop against a local engine checkout instead of the released package, replace the dependency with
   `[tool.poetry.dependencies] datenwissenschaften = { path = "<engine checkout>", develop = true }`.
2. **Configure the game** in `config.yaml`: `training.game: <Game>-Nes-v0`, `training.savestate: <state>`,
   `ui.release: local`.
3. **Replace the Airstriker example** with the game's files from the next sections: `src/ram/airstriker.py`
   becomes `src/ram/<game>.py`, `src/game/actions.py` gets the NES buttons, `src/states/survive.py` becomes
   the game's states, and the wrapper and its tests are renamed.
4. **Create `NOTES.md`**, run `ruff check`, `ruff format`, `pytest`, and commit.

Layout after the first iteration:

```
app.py                  LayaTrainer(Wrapper, CONFIG_PATH).train()
src/ram/<game>.py       GameRam(RamInfo) with ram(0x...) fields and describe()
src/game/actions.py     ACTION_TABLE (actions, frames, buttons) and ACTION_DESCRIPTIONS
src/game/vision.py      detectors built from assets/ templates and RAM positions
src/game/heading.py     maps an offset to the action that moves toward it (when movement is projected)
src/game/wrapper.py     StateMachineGymWrapper subclass wiring the above
src/states/             one State per phase, a shared base state, exploring vs targeted states
assets/                 template PNGs cut from real frames
tests/                  one test per mechanic: detection, reward, transition
NOTES.md                verified RAM addresses, mechanics, pitfalls, open questions
.claude/skills/         this skill and its scripts
```

The engine version is the engine maintainer's decision: never bump it from a game project.

## 2. Discover the RAM automatically, then verify

Never guess mechanics. Verify each one in the emulator and write it into `NOTES.md` with the evidence.

- **Discover everything first** with `scripts/ram_discover.py`; it needs only the game id:
  ```bash
  poetry run python .claude/skills/beat-nes-game/scripts/ram_discover.py --game <Game>-Nes-v0 --state <state> \
      --play-minutes 20 --playfield-bottom 224 --seed 0 --out discovery
  ```
  Set `--playfield-bottom` to the first HUD row when the HUD sits below the playfield. The resulting
  `discovery/ram_map.json` contains:
  - `known_variables`: stable-retro's `data.json` (lives, score, health or time for most NES games).
  - `position`: bytes that follow held directions from several points of the level, with the response to
    each direction. A byte reacting to two directions reveals projected (isometric) movement.
  - `player`: the player's sprite color, found automatically, and per axis the best single byte and the best
    byte difference (`(ram[a] - ram[b]) % 256`, typically ground minus jump height) with the screen offset and
    pixel errors. A difference is chosen only when it is clearly more accurate. Accept a formula with a
    median error of about 1 px.
  - `timers`: bytes that count down steadily while idle (level timers, often one byte per digit).
  - `events`: bytes that changed rarely during random play, classified as flag, counter up, counter down or
    rare value, each with a screenshot of its first change in `discovery/events/`. Look at the screenshots to
    name them (items, weight, keys, doors, lives, level, room).
  Mirrors are common: of equal candidates keep the lowest address. The CPU stack (0x100–0x1FF) and the
  sprite table (0x200–0x2FF) are excluded because games reuse them.
- **Write `src/ram/<game>.py`** from verified values only, with a `describe()` that returns what Laya needs
  (lives, timer, progress counters, flags), and pin each field with a test.
- **Refine a sprite position** with `scripts/ram_locate.py` when the automatic color is shared by other
  objects; it takes an explicit color and extra savestates:
  ```bash
  PYTHONPATH=. poetry run python .claude/skills/beat-nes-game/scripts/ram_locate.py --game <Game>-Nes-v0 --state <state> \
      --starts <extra.state> --actions src.game.actions:ACTION_TABLE --color <r,g,b> --min-area 70 \
      --max-fill 0.9 --playfield-bottom <row> --decisions 1500 --seed 0 --out locate.json
  ```
  Prefer RAM positions over color blobs: signs, pickups and HUD icons often share the player's colors.
- **Map the level** with `scripts/explore.py` (Go-Explore). It returns milestones (the first time each tracked
  RAM value appears, with a savestate and action path each), death hotspots and maxima:
  ```bash
  PYTHONPATH=. poetry run python .claude/skills/beat-nes-game/scripts/explore.py --game <Game>-Nes-v0 --state <state> \
      --start none --actions src.game.actions:ACTION_TABLE --cell <room>,<x>/24,<y>/24,<counter>,<flag> \
      --priority 0,0,0,4,20 --lives <lives address> --won <win flag address> --minutes 20 --seed 0 --out explore/
  ```
  Put the discovered progress bytes (counters, flags) in `--cell` with a high `--priority`. Continue from a
  milestone with `--start explore/<milestone>.state`. If a gate value is never reached, the state machine
  cannot pass that gate: fix the gate before training.
- **Test mechanics directly**: restore savestates with `env.em.set_state(bytes); env.data.reset();
  env.data.update_ram()` and poke RAM with `env.unwrapped.data.memory.assign(address, "|u1", value)`.
- **Prove every detector on real frames** from the level start and from later milestones: draw
  `state.detections()` with `datenwissenschaften.vision.overlay.draw_detections` and look at the image. Check
  both misses and false positives (same-colored signs, the player's own sprite, HUD, thin edges).
- **Prove every transition condition** by reaching it (explorer milestone or steering with the `move` hint)
  and reading the RAM change. A condition that never fires blocks the whole curriculum.

## 3. State machine

- One state per phase with a single goal: search for X, reach X, operate X, leave through X.
- `description` is Laya's question: one short line, `"You are the <hero>. <goal>. Which move?"`. Long
  questions cost tokens and overflow the stream panel.
- `describe()` gives only what the choice needs: the target with `visible`, `direction`, `distance`, and a
  `move` field naming the action that heads toward it (`last_seen` when it left the screen), the nearest
  enemy, a few RAM facts. Pretrained Laya follows such a `move` hint most of the time before any training.
- `_next()` returns the next state class only on a verified condition. `_won()` only in the final state.
- `_terminated()` on life loss and on damage the game counts.
- `_truncated()` after a fixed frame budget per state (for example 3600 frames, 60 s at 60 Hz).

## 4. Rewards

Each state trains its own Laya, and a transition ends that model's trajectory. So inside every state:

| Signal | Rule |
|---|---|
| Transition to the next state | the largest reward of the state (10); must beat anything farmable before it |
| Winning the level | 20 in the final state |
| Approach | potential-based: `0.05 × pixels closer`, ignore jumps above the target-switch distance (24 px) |
| Progress | only for verified RAM progress (items +1, progress counters +2) |
| Exploration | only in searching states: new screen +1, new 16 px spot +0.1 |
| Failure | −10 on life or damage loss, ends the episode |
| Step cost | 0.002 per frame, so a full 3600-frame timeout costs about −7 |

Check each state: finishing fast beats wandering until the timeout, dying is worse than timing out, and no
loop can farm reward (approach rewards are refunded when moving away). Episode scores accumulate across the
curriculum: a checkpoint stores the score that reached it and episodes starting there continue from it.

## 5. Actions

- `ACTION_TABLE` has shape `(actions, frames, buttons)` in the order of `env.buttons`; 4 frames per decision
  works well.
- Hold movement buttons for all frames; tap edge-triggered buttons (fire, jump, attack) on frame 0 only.
- Name actions by what they do on screen (`up-right`, not `UP`) and map offsets to them in `heading.py`
  when the game projects movement (read the projection from the `position` responses of the discovery).

## 6. How Laya learns in the engine (verify before changing)

- One checkpoint per state: `<paths.models>/<game>/<savestate>/<State>/laya.pt` (weights, 8-bit AdamW,
  trust region, trained decisions). The active state's model is swapped into the single GPU slot.
- Options are shuffled by a stable hash of state and question. Without it Laya gives about 97% to the first
  listed option and every fresh model starts stuck on one action.
- Group-relative policy gradient with importance weights for the exploration mixture (20% random actions,
  annealed to 5% over 50k decisions). Keep the importance weights: without them the policy saturates on
  wrong choices.
- The trust region targets KL 0.01 per update: it grows the step by the square root of the shortfall (at most
  ×10) and shrinks it on overshoot; an overshooting update is blended back toward a CPU weight snapshot.
- Float16 GPUs (for example Turing, RTX 20xx) need learning-rate scales around 10³–10⁴; bfloat16 is noisier
  (7-bit mantissa) and relies on backtracking.
- The entropy bonus is a small constant (0.001). An adaptive entropy target pushed every model toward
  uniform play and unlearned correct choices.
- Changing what a model sees (option order, observation layout) requires a new `MODEL_LAYOUT` value in
  `training/identity.py`; training then starts fresh once. Never use the engine version for this.

## 7. Diagnose a run

Read `http://<ui host>/api/snapshot` (`metadata.model.laya`, `metadata.savestate_curriculum`, `summary`,
`server.release`) and `/api/live/episode`, `/api/live/frames?episode=<id>&start=<n>` (per-frame status with
probabilities, action and state, and JPEG frames to look at).

| Symptom | Cause | Action |
|---|---|---|
| One action at 100%, entropy near 0 | collapse | check option shuffle, importance weights, trust region; start the state fresh |
| `learning_rate_scale` at its maximum, `kl` far below 0.01 | steps too small | widen the scale range |
| Probabilities near uniform for a long time | entropy pressure or no reward signal | check the entropy constant and the state's rewards |
| Episodes end in seconds at about −10 | early damage or death | watch replays for the hazard; add it to `describe()` |
| Episodes time out at about −7 in a searching state | target never seen | verify the detector on that screen; check the exploration reward |
| A state never gains wins | transition condition never fires | reproduce with the explorer or steering, then fix the condition |
| Curriculum checkpoint deleted repeatedly | score stagnation from a bad start | inspect the checkpoint frame |

## 8. Deploy

- Build an image from the package plus the committed engine (a Dockerfile with a Node stage for the
  dashboard, `python -m stable_retro.import roms`, `ffmpeg`, and GPU access), for example with Dokku
  (`--gpus=all`, persistent storage for the `working/` directory, wait-to-retire 0 so two containers never
  share the GPU). When training against a local engine checkout, commit it first; never commit `config.yaml` with API keys or ROMs.
- Stamp every deploy with a CalVer release `YYYY.MM.DD-N` (N counts the day's deploys, kept on the server,
  for example as a Dokku config value) written into `ui.release`. The stream shows it as the Laya model and
  reloads itself when it changes, so a running live stream picks up every deploy.
- Keep training data, the Docker data root and the containerd root on a large data disk and prune the build
  cache (`docker builder prune -af`) regularly: every deploy of the image adds gigabytes.
- A push that is interrupted locally can keep building on the server: make sure the old build is gone
  before pushing again.
- Deploying restarts training from the saved state checkpoints.

## 9. Regular optimization run

Run this loop on a schedule for each game project, one change per run:

1. Read the snapshot and the last episodes. Record per state: wins/target, trained decisions, entropy, KL,
   learning-rate scale, typical end reason (win, damage, death, timeout).
2. Pick the earliest state that is not mastered. Look at two recent replays of it (frames plus status).
3. Find the single biggest blocker with the table in section 7. If it is a game mechanic, reproduce it
   offline (discovery, explorer, steering, RAM poke) before touching code.
4. Make the smallest fix in the game package (detector, `describe()`, reward, transition, question), or in the
   engine only when it applies to every game. Add or update a test that pins the mechanic.
5. `ruff check`, `ruff format`, `pytest` in this project (and the engine when it changed), then commit with a message that states
   the evidence, and deploy.
6. After the next update cycle, confirm the metric moved; revert the change if it made the state worse.
7. Update `NOTES.md` with what was verified, what was ruled out, and the next open question.

Guardrails: never bump the engine version, never delete training data or reset models without the owner's
request, never commit secrets or ROMs, and keep every commit buildable.
