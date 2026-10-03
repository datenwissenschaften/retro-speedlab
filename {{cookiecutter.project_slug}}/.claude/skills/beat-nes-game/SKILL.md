---
name: beat-nes-game
description: Turn this generated retro-speedlab project into a game package (automatic RAM discovery), research online how each level is beaten and reproduce it, learn the game's mechanics, enemies and power-ups, map each level and where it is safe, design the state machine, hints and rewards, then train, diagnose and regularly optimize a retro-speedlab game package that beats an NES level with Laya (one Laya model per state machine state). Use when creating a new game package, when a game's training stalls or collapses, when asked to review rewards, hints, detections or curriculum progress, or on a scheduled optimization run for a game project.
---

# Beat an NES game with Laya

This project was generated from the retro-speedlab template as a skeleton that knows nothing about the game
yet: one `Play` state, the plain NES buttons, an empty `GameRam` and no rewards. It
depends on `retro-speedlab-core` (the engine, `datenwissenschaften` on PyPI,
https://github.com/datenwissenschaften/retro-speedlab-core) and contains only game knowledge: RAM map,
detectors, actions, states, hints, rewards. The engine owns learning, curriculum, UI and deployment. Work in
small verified steps, follow the engine's `AGENTS.md` (no defaults, fail fast, ruff, loguru, python-box, no
comments), and record every verified game fact in `NOTES.md`.

The order matters: first research how the game is beaten, verify it and understand the whole game, then
design states, hints and rewards from that understanding, then prove that a player who only follows the hints
can win, and only then train.

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
   Read `scenario.json`: its done condition (often `lives` negative) ends every episode, whatever the states say.
   To develop against a local engine checkout instead of the released package, replace the dependency with
   `[tool.poetry.dependencies] datenwissenschaften = { path = "<engine checkout>", develop = true }`.
2. **Configure the game** in `config.yaml`: `training.game: <Game>-Nes-v0`, `training.savestates: [<state>]`,
   `ui.release: local`.
3. **Grow the skeleton** with the game's files from the next sections: verified fields go into `GameRam` in
   `src/ram/game.py`, `src/game/actions.py` refines the plain NES buttons, and `Play` in `src/states/play.py`
   splits into the game's states, each with a test.
4. **Create `NOTES.md`**, run `ruff check`, `ruff format`, `pytest`, and commit.

Layout after the first iteration:

```
app.py                  LayaTrainer(Wrapper, CONFIG_PATH).train()
src/ram/game.py         GameRam(RamInfo) with ram(0x...) fields and describe()
src/game/actions.py     ACTION_TABLE (actions, frames, buttons) and ACTION_DESCRIPTIONS
src/game/vision.py      detectors built from assets/ templates and RAM positions
src/game/heading.py     maps an offset to the action that moves toward it (when movement is projected)
src/game/hints.py       every suggested action and nothing else (section 5)
src/game/wrapper.py     StateMachineGymWrapper subclass wiring the above
src/states/             one State per phase, a shared base state, exploring vs targeted states
assets/                 template PNGs cut from real frames: targets, enemies, power-ups
tests/                  one test per mechanic: detection, hint, reward, transition
NOTES.md                verified RAM addresses, mechanics, catalogue, pitfalls, open questions
.claude/skills/         this skill and its scripts
```

The engine version is the engine maintainer's decision: never bump it from a game project.

## 2. Learn the whole game before writing states

Never guess mechanics. Learn them from published sources, verify each one in the emulator and write it into
`NOTES.md` with the evidence. A state machine built on a wrong mechanic cannot be trained into a win: in Snake
Rattle 'n' Roll the weight drain while entering the exit counted as damage and ended every winning attempt
before the win flag set.

### Research how each level is beaten

Before measuring anything, find out from published sources what a player has to do to beat the level being
trained. Use `WebSearch` and `WebFetch`:

- **Walkthroughs, guides and the original manual** (GameFAQs, StrategyWiki, fan sites, manual scans): the
  level's goal, the order of its gates (what opens the exit), the items, enemies and hazards, and how the level
  ends.
- **RAM maps** (Data Crystal, TASVideos game resources): candidate addresses for lives, position, level,
  timers and progress flags.
- **Speedruns and tool-assisted runs** (speedrun.com, TASVideos submissions and their videos): the fastest
  route and the tricks that skip parts of it, for the speedrun phase later.

Write the findings into `NOTES.md` under `## Walkthrough`, one subsection per level: numbered steps from the
level start to the level end, each with its source URL, and the candidate RAM addresses with theirs. Mark every
step and address `unverified` until it is measured.

Tag every step as a **gate** or **optional**. A gate is a step the level cannot be finished without: what opens
the exit and what that needs first (reach a weight, ring a bell, collect a key, defeat a boss, enter the door).
Everything else is optional: points, bonus items, extra lives, enemies and hazards that can be avoided. Optional
steps wait until every gate of the level is rewarded, unless one blocks a gate (an item the gate needs, a hazard
that ends the attempts before the gate).

Published knowledge is a hypothesis, not a fact:

- **Verify each step in the emulator** before building on it (RAM discovery and gate tests below). When the
  emulator disagrees with a source, the emulator wins: note the conflict and correct the step.
- **Reproduce the walkthrough.** A scripted player built on the verified RAM (position, targets, flags) plays
  the steps from the start savestate to the level end, saving a savestate at each gate. When it cannot beat
  the level, Laya cannot learn to: find the step that fails and fix the understanding before training.
- **Teach the behaviour, not the moves.** The verified steps become the gates of the state machine (section
  3), the targets to mark (markers) and the progress rewards (section 4); the engine's curriculum then starts
  episodes where each mastered phase ends, so Laya is told about and rewarded for each step and learns to reproduce it. Hints stay generic rules (section 5):
  never copy coordinates, routes or button sequences from a source into the game package.

### RAM discovery

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
- **Build a world location** from screen and position bytes (signed high byte × 256 + low byte per axis) and
  check that it is continuous while walking. Hints, routes and exploration all depend on it.
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

### Map the level and its gates

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
- **List every gate** of the level, starting from the walkthrough's gate steps: what must happen before the
  next part opens (eat to a weight, ring a bell, collect a key, defeat a boss), and what undoes it (a hit costs
  weight, a death resets a counter).
- **Test mechanics directly**: restore savestates with `env.em.set_state(bytes); env.data.reset();
  env.data.update_ram()` and poke RAM with `env.unwrapped.data.memory.assign(address, "|u1", value)`. Leave
  the player idle for a few thousand frames at each gate to separate time-based effects from damage.
- **Time the win**: record every frame from entering the exit to the win flag. Flags often set many frames
  after other bytes change (the Snake Rattle 'n' Roll win flag set 78 frames after the weight started draining
  into the door); anything that ends the attempt earlier hides the win.

### Catalogue enemies, power-ups and hazards

Laya only knows what `describe()` tells it, so every object that hurts or helps must be detected.

1. **Collect frames**: play from the level start and from each milestone, and dump frames around every damage
   event (the lives or health byte drops) and every pickup (a counter rises). Tile them into contact sheets
   (`ffmpeg -i run.mp4 -vf "fps=1,scale=160:-1,tile=8x6" sheet_%02d.png`) and look at them.
2. **Name every object**: each enemy type (land, water, air, stomping, bosses), each power-up (extra time,
   extra life, points, speed, invincibility, food), and each hazard that is part of the level (water, pits,
   spikes, waterfalls). Write the list into `NOTES.md` with where it appears and what it does, verified by
   touching it in the emulator.
3. **Cut templates** from real frames into `assets/` (one PNG per sprite pose that differs; tight crop, no
   background where possible) and add them to the matching `TemplateDetector` in `vision.py`: one detector
   for enemies, one for power-ups, one per target.
4. **Prove each detector** on frames from the level start and from later milestones: draw
   `state.detections()` with `datenwissenschaften.vision.overlay.draw_detections` and look at the image. Check
   both misses and false positives (same-colored signs, the player's own sprite, HUD, thin edges). Pin each
   template with a test that renders it into a blank frame.
5. **Hazards without sprites** (water, pits) are detected by color or RAM (for example the fraction of the
   water color around the player); state them as facts (`in_water`), not as advice.

When the user names an object you cannot find in the recordings, ask for a screenshot or the place it
appears instead of guessing a sprite.

### Pitfalls

- **Replays of `.bk2` recordings can drift** from the live run (curriculum restores, reset timing). Never
  analyse training behaviour from `.bk2` replays; use the live per-frame status
  (`/api/live/frames`) or runs started from savestates.
- **`scenario.json` ends episodes** on its own condition; the state machine cannot keep an episode alive past it.
- **Game-over and continue screens** change RAM (lives reset, flags flip). Only trust flags inside play.

## 3. Develop the state machine yourself

Derive the states from the gates, not from a template: one state per gate, in the order the game enforces.

- One state per phase with a single goal: search for X, reach X, operate X, leave through X.
- `description` is Laya's question: one short line, `"You are the <hero>. <goal>. Which move?"`. Long
  questions cost tokens and overflow the stream panel.
- `describe()` gives facts only: the target with `visible`, `direction`, `distance`, the nearest enemy and
  power-up, hazards, a few RAM facts. Advice is merged in from `hints.py` (section 5).
- Split transitions into `_advance()` (the verified forward condition) and `_fallback()` (a lost
  precondition sends the snake back, for example losing weight before the scale rang goes back to eating).
  `_next()` returns the fallback first. Only forward transitions pay the transition reward; the engine ignores
  backward transitions for curriculum success and checkpoints.
- `_won()` only in the final state, on the verified win flag.
- `_terminated()` only on game over. Lost lives and hits cost reward but the attempt continues from the
  respawn, so later parts of the level are practised instead of restarting from the beginning.
- `_truncated()` after a fixed frame budget per state (for example 3600 frames, 60 s at 60 Hz).
- The final state must not treat what the exit does to the player as damage (entering the door drained the
  weight to zero).

## 4. Rewards

Each state trains its own Laya, and a transition ends that model's trajectory. So inside every state:

| Signal | Rule |
|---|---|
| Transition to the next state | the largest reward of the state (10); must beat anything farmable before it; never for a fallback |
| Winning the level | 20 in the final state |
| Approach | potential-based: `0.05 × pixels closer` to a visible target, or to the route waypoint when the target is remembered; ignore jumps above the target-switch distance (24 px) |
| Progress | only for verified RAM progress (items +1, progress counters +2) |
| Exploration | only in searching states and only until a route to the target is known: new screen +1, new 16 px spot +0.1, decaying with visits across attempts |
| Hit | −5 per unit of health, weight or armour lost, in every state except where the game itself drains it |
| Lost life | −10, the attempt continues |
| Game over | ends the attempt |
| Step cost | 0.002 per frame, so a full 3600-frame timeout costs about −7 |

Check each state: finishing fast beats wandering until the timeout, dying is worse than timing out, no loop
can farm reward (approach rewards are refunded when moving away, fallbacks pay nothing), and damage is
compared with the previous frame so a respawn is not charged twice.

## 5. Hints

A hint is anything that suggests an action. Keep all of them in `src/game/hints.py` and nowhere else, so
anyone can see what is advice and what Laya learns. States only merge the hint dictionaries into
`describe()`. Pretrained Laya follows a `move` hint most of the time before any training, which is what makes
the first wins possible.

Hints must be generic rules that work in every level of the game, never level knowledge:

| Hint | Rule |
|---|---|
| `move` to a visible target | the action whose screen direction best matches the offset to the nearest target |
| `move` along a route | when the target is off screen but was seen before, head for the route waypoint about 48 px ahead |
| `remembered` | the target is off screen and its place is known |
| attack or eat (`tongue`) | the target is within reach and straight ahead in the facing direction |
| `blocked` / `jump` | while stuck (no movement for 12 frames), alternate every 12 frames between jumping and pushing on; a jump from standstill alone never frees the player |
| `move_away`, `ahead` | a close enemy (under 48 px): the escape direction and whether it is in the facing direction |
| `move` while exploring (`exploring`) | a searching state without any known target heads for the least visited neighbouring cell that the safety map does not mark as dangerous or blocked |
| `unsafe` | the directions whose next cell has hurt the player before, from the safety map (section 6) |

**Routes are learned, not written.** Straight lines to a remembered place run into walls and ledges. The
engine's `Landmarks` records the trail a state walked (a point every 8 px, restarted on respawn jumps) when it
first sees its target, removes loops, keeps the shortest route, and `waypoint()` returns the next point on it.
Never hardcode coordinates, routes or seeds into the game package.

**Prove the hints before training.** Write a scripted player that does exactly what the hints say (plus
`jump` when an enemy is `ahead`) and run it through the whole level from the start savestate with the state
machine. If it cannot win, Laya cannot learn a win from those hints: find where it gets stuck, look at the
frame, and fix the state, hint or detector first. Measure afterwards how often Laya follows each state's hint
(section 9) to see what it learned beyond them. Run it in every level you train, several attempts in a row
with shared memory, because exploring and the safety map only pay off across attempts.

## 6. Map the level and learn where it is safe

The player must understand the level as a map: where it is, where it has been, where things hurt and where it
cannot go. Build that map from the player's own play, in world coordinates, and keep it per level.

- **World coordinates first.** Combine screen and position bytes into one continuous location (section 2)
  and use it for everything spatial: routes, exploration, safety, danger spots on the stream.
- **One map per level (savestate)**, stored next to the level's landmarks (the engine's
  `Landmarks.safety`, a `SafetyMap` in 16 px cells) so it survives restarts and deploys and is cleared by a
  model reset.
- **Record what happens where**: every hit or lost life marks its cell as `danger`; every cell the player got
  stuck pushing toward marks `blocked`. Only damage the game really deals counts (not the exit draining
  weight). Record facts, never hand-entered coordinates.
- **Exploration memory**: count visits per cell across attempts. A searching state without a target heads for
  the least visited neighbouring cell, weighted by the map (danger 20, blocked 10 visits), so the player works
  its way along the frontier instead of pushing into the first wall. Mark the direction the hint suggested,
  not the direction the player last moved, when it gets stuck: after hitting a wall the player still faces
  the way it came.
- **Use the map in hints, not as a hidden script**: `unsafe` directions, the exploring `move`, routes around
  blocked cells. Laya still decides; rewards stay the same (hits −5, lives −10).
- **Look at the map**: dump the danger and blocked cells of a level and compare them with the danger spots on
  the stream and with frames at those coordinates. Clusters of danger reveal hazards or enemies that need a
  detector; long blocked walls reveal ledges that need a jump.
- **Test it**: a hit marks its cell, a restart keeps the map, a reset clears it, and the exploring hint
  avoids a marked cell.

## 7. Actions

- `ACTION_TABLE` has shape `(actions, frames, buttons)` in the order of `env.buttons`; 4 frames per decision
  works well.
- Hold movement buttons for all frames; tap edge-triggered buttons (fire, jump, attack) on frame 0 only.
- Name actions by what they do on screen (`up-right`, not `UP`) and map offsets to them in `heading.py`
  when the game projects movement (read the projection from the `position` responses of the discovery).
- Test whether the action set can pass every obstacle (a tapped jump from standstill lands on the same spot;
  jumping onto ledges may need the direction held). Changing actions changes the models' options and needs a
  fresh start.

## 8. How Laya learns in the engine (verify before changing)

- One checkpoint per state: `<paths.models>/<game>/<savestate>/<State>/laya.pt` (weights, 8-bit AdamW,
  trust region, trained decisions). The active state's model is swapped into the single GPU slot; the next
  state's checkpoint is prefetched into RAM and saves are written in the background.
- Once every state is mastered, every episode is a full run from the start savestate, and each state's model
  takes over when its phase begins.
- Levels are trained in order: `training.savestates` lists them, and the first level without 8 full-run wins is
  trained until it has them, then the next. Only when every level is beaten do the levels take turns every
  `training.rotation_minutes` (2 hours) as speedruns, with an extra cost of 0.005 per frame so faster wins
  score higher. The current level and turn survive restarts and deploys.
- Each level keeps its own models, curriculum savestates, landmarks, routes, safety map, story and statistics.
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
- Changing what a model sees (option order, observation layout, action or question texts) requires a new
  `MODEL_LAYOUT` value in `training/identity.py`; training then starts fresh once. Moving code (for example
  into `hints.py`) without changing the observation needs no reset. Never use the engine version for this.

## 9. Diagnose a run

Read `http://<ui host>/api/snapshot` (`metadata.model.laya`, `metadata.savestate_curriculum`, `summary`
with `full_run_episodes` and `full_run_wins`, `server.release`) and `/api/live/episode`,
`/api/live/frames?generation=<g>&episode=<id>&start=<n>` (per-frame status with probabilities, action, state,
observation and events, and JPEG frames to look at).

Compute per state from the live frames: how often the chosen action equals the hinted `move`, the average
probability of the hinted move, weight and life changes with the frame they happen on, and time in water or
stuck.

| Symptom | Cause | Action |
|---|---|---|
| One action at 100%, entropy near 0 | collapse | check option shuffle, importance weights, trust region; start the state fresh |
| `learning_rate_scale` at its maximum, `kl` far below 0.01 | steps too small | widen the scale range |
| Probabilities near uniform for a long time | entropy pressure or no reward signal | check the entropy constant and the state's rewards |
| Laya ignores the hint in a searching state | exploration reward pulls elsewhere | stop exploration once a route is known |
| Stuck at the same place until the timeout | straight-line hint into a wall | check the route and the stuck alternation with the scripted player |
| Stuck in the first corner of a new level | no target known, no hint | check the exploring hint and that stuck directions are marked `blocked` |
| Repeated hits at the same place | undetected enemy or hazard | find it in the frames and the safety map, add a template, verify |
| Weight or health drains steadily | hazard or time effect | reproduce idle and in the hazard, then add it as a fact |
| Episodes time out in a searching state | target never seen | verify the detector on that screen; check the exploration reward |
| A state never gains wins | transition condition never fires | reproduce with the explorer or steering, then fix the condition |
| The player reaches the exit but no win | the attempt ends before the win flag | time the win (section 2) and stop charging what the exit does |
| Curriculum checkpoint deleted repeatedly | score stagnation from a bad start | inspect the checkpoint frame |

## 10. Deploy

- Build an image from the package plus the committed engine (a Dockerfile with a Node stage for the
  dashboard, `python -m stable_retro.import roms`, `ffmpeg`, and GPU access), for example with Dokku
  (`--gpus=all`, persistent storage for the `working/` directory, wait-to-retire 0 so two containers never
  share the GPU). When training against a local engine checkout, commit it first; never commit `config.yaml`
  with API keys or ROMs.
- Stamp every deploy with a CalVer release `YYYY.MM.DD-N` (N counts the day's deploys, kept on the server,
  for example as a Dokku config value) written into `ui.release`. The stream shows it as the Laya model and
  reloads itself when it changes, so a running live stream picks up every deploy.
- Keep training data, the Docker data root and the containerd root on a large data disk. Keep the build
  cache: a scheduled `docker builder prune -af` makes the next deploy rebuild every layer (15 minutes and
  more with the CUDA wheels). Prune only by age (`docker builder prune -f --filter until=168h`) or by hand.
- A push that is interrupted locally can keep building on the server: make sure the old build is gone
  before pushing again.
- Deploying restarts training from the saved state checkpoints. Recording numbers restart too, so copy a
  recording you need before the next deploy overwrites it.
- The stream plays every attempt to its end. Between new attempts it shows random full or successful runs,
  labelled as replays and not live training.

## 11. Scheduled autonomous runs on the server

The project trains on the server around the clock as a Dokku app, and several times a day Dokku's scheduler (a
`cron` entry in `app.json`, generated by `dokku/deploy.sh` from `agent.schedule` in `config.yaml`) starts
Claude Code headless in a one-off container of that app (`agent/daily.sh`, prompt in `agent/PROMPT.md`) to
check progress, change the code and keep learning. The repositories are mounted into the container at
`/workspace` and are the source on the server; the token lives in the app's Dokku config
(`CLAUDE_CODE_OAUTH_TOKEN`). Every deploy and schedule value comes from `config.yaml`, nothing is set in
scripts.

1. **Measure.** Read the dashboard (`/api/snapshot`: per-level summary in `summary.by_savestate`,
   `metadata.curricula`, `metadata.stories`, `metadata.run`), the live attempts (`/api/live/episode`,
   `/api/live/frames`), and per level the landmarks, routes and safety map in the training data. Compare with
   the last reports in `agent/reports/`. Record per level: attempts, full-run wins, the curriculum phase that
   blocks, where attempts end, hint-following rate, the action probabilities, and whether the previous run's
   change moved its metric.
2. **Decide the change.** Pick the level being trained (the first unbeaten one) and its biggest blocker with
   the table in section 9. A constant reward is always the first blocker: without a learning signal every
   action stays equally likely. Revert the previous run's change first if its metric got worse. When
   `NOTES.md` has no walkthrough for the level, research it first (section 2); afterwards the next blocker is
   the first **gate** of the walkthrough that is not yet measured, marked, reached by the scripted player and
   rewarded as its own phase. Skip optional steps until every gate of the level is done, unless one blocks a
   gate. Before working on what leads up to a gate, measure whether its condition is already met: in the live
   frames and the scripted player, check the value the gate needs (a weight, an item count, a key flag). When
   attempts already reach it, the gate itself (the scale, the door, the boss) is the next work, not its
   preparation.
3. **Reproduce before fixing.** Copy savestates and landmarks from the training data and reproduce the
   blocker in the emulator (scripted hint player, explorer, hit capture, RAM diff). Never guess sprites,
   mechanics or coordinates; cut templates from real frames and verify them.
4. **Fix, test, ship.** The smallest change in the game package (or in the engine when it applies to every
   game), with a test that pins it. `ruff check`, `ruff format`, `pytest`, commit with the evidence in the
   message, deploy, and watch the live training for 10 minutes: no errors, non-zero rewards, action
   probabilities no longer uniform. When an investigation is inconclusive, try another way and narrow the
   change to what is verified instead of stopping.
   **Never end the run before the time to stop exploring.** Check it with `date -u` against the run's start
   and `agent.hours`. One shipped change is not the end of a run: after each verified deploy, take the same
   gate one step further (measure, mark, reach, phase) and ship again; when the gate is done, start the next
   gate. Only the final report and summary come after the cutoff.
5. **Grow the game.** When a level is beaten and the next level has no savestate yet, create it: play from the
   level's winning checkpoint through the level end, find the RAM that marks the new level, save the emulator
   state at its start as `savestates/LevelN.state` (gzip, like stable-retro states), verify it loads, and
   append it to `training.savestates` in both configs. Research the new level's walkthrough. New levels may
   need new states, enemies, power-ups or hazards: catalogue them (section 2) before training on them.
6. **Report.** Write `agent/reports/YYYY-MM-DDTHHMM.md` (the run's UTC start): the measurements, the decision
   and its evidence, every change with its commit and its live check, the metric for the next run, and open
   questions. Update `NOTES.md` with verified facts.

Rules for the unattended run: ship at least one verified change that improves what the model learns from;
never reset models, delete training data or edit files of the running training; never bump the engine
version; never commit secrets or ROMs; do not deploy when tests fail, and revert when a deploy breaks.

Guardrails: never bump the engine version, never delete training data or reset models without the owner's
request, never commit secrets or ROMs, never hardcode level knowledge into hints, and keep every commit
buildable.
