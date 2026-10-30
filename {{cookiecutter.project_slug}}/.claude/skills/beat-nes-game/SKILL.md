---
name: beat-nes-game
description: Turn this generated retro-speedlab project into a game package (automatic RAM discovery), research online how each level is beaten and how speedruns route it, learn the game's mechanics, enemies and power-ups, map each level, design the state machine, rewards and dynamics() the speedrun search reads, then diagnose and improve the search's movie. Use when creating a new game package, when the speedrun search is stuck or stalls, when asked to review states or rewards, or on a scheduled lab run for a game project.
---

# Beat an NES game with the speedrun search

This project was generated from the retro-speedlab template as a skeleton that knows nothing about the game
yet: one `Play` state, the plain NES buttons, an empty `GameRam` and no rewards. It
depends on `retro-speedlab-core` (the engine, `datenwissenschaften`,
https://github.com/datenwissenschaften/retro-speedlab-core) and contains only game knowledge: RAM map,
actions, states, rewards and `dynamics()`. The engine owns the search, the movie, the stream and deployment.
Work in small verified steps, follow the engine's `AGENTS.md` (no defaults, fail fast, ruff, loguru,
python-box), and record every verified game fact in `NOTES.md` (the whole game) or `notes/level<N>.md` (one
level).

The order matters: first research how the game is beaten and how speedruns route it, verify it and understand
the whole game, then design states and rewards from that understanding, and only then let the search run.

Run every command from the project root. Placeholders used below:

| Placeholder | Meaning |
|---|---|
| `<Game>-Nes-v0` | the stable-retro game id, for example `SuperMarioBros-Nes-v0` |
| `<start>` | `none` for power-on, or a state file you saved yourself after playing from power-on |
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
   Read `scenario.json` for the RAM variables it names; the engine ignores its done condition.
2. **Configure the game** in `config.yaml`: `training.game: <Game>-Nes-v0`, `ui.release: local`.
   There are no savestates to configure: every movie boots the game at power-on.
3. **Grow the skeleton** with the game's files from the next sections: verified fields go into `GameRam` in
   `src/ram/game.py`, `src/game/actions.py` refines the plain NES buttons, and `Play` in `src/states/play.py`
   splits into the game's states, each with a test.
4. **Create `NOTES.md` and `notes/level1.md`**, run `ruff check`, `ruff format`, `pytest`, and commit.

Layout after the first iteration:

```
app.py                  Flyte workflows: speedrun (the default) and lab
src/ram/game.py         GameRam(RamInfo) with ram(0x...) fields, position(), remaining_lives() and dynamics()
src/game/actions.py     ACTION_TABLE (actions, frames, buttons)
src/game/wrapper.py     StateMachineGymWrapper subclass wiring the above
src/states/             one State per phase, each with a one-line goal
tests/                  one test per mechanic: reward, transition, RAM value
NOTES.md                verified RAM addresses, mechanics and pitfalls of the whole game
notes/level<N>.md       one level: a short `## Now` header (status, blocker, open questions), then its dated log
.claude/skills/         this skill and its scripts
```

The engine version is the engine maintainer's decision: never bump it from a game project.

## 2. Learn the whole game before writing states

Never guess mechanics. Learn them from published sources, verify each one in the emulator and write it into
the notes with the evidence. A state machine built on a wrong mechanic sends the search the wrong way: in one
game a resource draining while entering the exit counted as damage and ended every winning branch before
the win flag set.

### Research how each level is beaten

Before measuring anything, find out from published sources what a player has to do to beat the level, and how
the fastest runs route it, with `WebSearch` and `WebFetch`:

- **Videos** (YouTube speedruns, TASVideos encodes, speedrun.com, World of Longplays): the route, the places
  of each objective and the tricks that skip parts; the inputs where an input display shows them. Never replay
  a movie file's inputs, they do not sync in `stable_retro`.
- **Walkthroughs, guides and the original manual** (GameFAQs, StrategyWiki, fan sites, manual scans): the
  level's goal, the order of its gates (what opens the exit), the items, enemies and hazards, and how the level
  ends.
- **RAM maps** (Data Crystal, TASVideos game resources): candidate addresses for lives, position, level,
  timers and progress flags.

Write the findings into each level's `notes/level<N>.md` under `## Walkthrough`: numbered steps from the
level start to the level end, each with its source URL, and the candidate RAM addresses with theirs. Mark every
step and address `unverified` until it is measured.

Tag every step as a **gate** or **optional**. A gate is a step the level cannot be finished without: what opens
the exit and what that needs first (reach a weight, ring a bell, collect a key, defeat a boss, enter the door).
Everything else is optional and only slows a speedrun down, unless it blocks a gate.

Published knowledge is a hypothesis, not a fact: verify each step in the emulator before building on it (RAM
discovery and gate tests below). When the emulator disagrees with a source, the emulator wins: note the
conflict and correct the step. The verified gates become the states (section 3) and the rewards (section 4);
never copy button sequences into the game package.

### RAM discovery

- **Discover everything first** with `scripts/ram_discover.py`; it needs only the game id:
  ```bash
  poetry run python .claude/skills/beat-nes-game/scripts/ram_discover.py --game <Game>-Nes-v0 --start <start> \
      --play-minutes 20 --playfield-bottom 224 --seed 0 --out discovery
  ```
  Set `--playfield-bottom` to the first HUD row when the HUD sits below the playfield. The resulting
  `discovery/ram_map.json` contains:
  - `known_variables`: stable-retro's `data.json` (lives, score, health or time for most NES games).
  - `position`: bytes that follow held directions from several points of the level, with the response to
    each direction. A byte reacting to two directions reveals projected (isometric) movement.
  - `player`: the player's sprite color, found automatically, and per axis the best single byte and the best
    byte difference (`(ram[a] - ram[b]) % 256`, typically ground minus jump height) with the screen offset and
    pixel errors.
  - `timers`: bytes that count down steadily while idle (level timers, often one byte per digit).
  - `events`: bytes that changed rarely during random play, classified as flag, counter up, counter down or
    rare value, each with a screenshot of its first change in `discovery/events/`. Look at the screenshots to
    name them (items, weight, keys, doors, lives, level, room).
  Mirrors are common: of equal candidates keep the lowest address. The CPU stack (0x100–0x1FF) and the
  sprite table (0x200–0x2FF) are excluded because games reuse them.
- **Build a world location** from screen and position bytes (signed high byte × 256 + low byte per axis) and
  check that it is continuous while walking.
- **Return it from `GameRam.position()`** as `Position(area, x, y, height, airborne)` from
  `datenwissenschaften.route.position`: `area` is the level or room, `height` and `airborne` are the jump height
  and whether the player is off the ground (0 and `False` in games without jumping). Return `None` outside play
  (title, bonus stage, death animation, off the map). The search keys its cells on it and the route memory
  reads it; without it the search only sees time buckets.
- **Return the life count from `GameRam.remaining_lives()`**: the lives the player has left, as the screen shows
  them (0 when the last one is gone). The search drops a branch on the frame the count drops. Read it only from
  verified bytes and return `None` where they are not valid (title, game-over and continue screens). A count
  that drops without a death (a mirror, a byte reused in a bonus stage) drops good branches: check it on frames
  of a real death and of a long run without one.
- **Return `GameRam.dynamics()`**: the coarsest tuple that tells good cells from bad ones beyond the position
  (what the player collected, the nearest moving object's offset, a platform's phase). The search keeps one
  savestate per cell, so a missing value merges cells that should differ.
- **Write `src/ram/<game>.py`** from verified values only and pin each field with a test.
- **Refine a sprite position** with `scripts/ram_locate.py` when the automatic color is shared by other
  objects; it takes an explicit color and states you saved from power-on:
  ```bash
  PYTHONPATH=. poetry run python .claude/skills/beat-nes-game/scripts/ram_locate.py --game <Game>-Nes-v0 \
      --starts <saved.state> --actions src.game.actions:ACTION_TABLE --color <r,g,b> --min-area 70 \
      --max-fill 0.9 --playfield-bottom <row> --decisions 1500 --seed 0 --out locate.json
  ```

### Map the level and its gates

- **Map the level** with `scripts/explore.py` (Go-Explore). It returns milestones (the first time each tracked
  RAM value appears, with a saved state and action path each), death hotspots and maxima:
  ```bash
  PYTHONPATH=. poetry run python .claude/skills/beat-nes-game/scripts/explore.py --game <Game>-Nes-v0 \
      --start <start> --actions src.game.actions:ACTION_TABLE --cell <room>,<x>/24,<y>/24,<counter>,<flag> \
      --priority 0,0,0,4,20 --lives <lives address> --won <win flag address> --minutes 20 --seed 0 --out explore/
  ```
  Put the discovered progress bytes (counters, flags) in `--cell` with a high `--priority`. Continue from a
  milestone with `--start explore/<milestone>.state`. If a gate value is never reached, the state machine
  cannot pass that gate: fix the gate first.
- **List every gate** of the level: what must happen before the next part opens, and what undoes it (a hit
  costs weight, a death resets a counter).
- **Test mechanics directly**: restore states you saved from power-on with `env.em.set_state(bytes); env.data.reset();
  env.data.update_ram()` and poke RAM with `env.data.memory.assign(address, "|u1", value)`. Leave the player
  idle for a few thousand frames at each gate to separate time-based effects from damage.
- **Time the win**: record every frame from entering the exit to the win flag. Flags often set many frames
  after other bytes change; anything that ends the branch earlier hides the win.
- **Catalogue enemies, power-ups and hazards** from frames around every damage event and every pickup: name
  each, write where it appears and what it does into the level's notes, verified by touching it in the emulator.

### Pitfalls

- **`scenario.json`'s done condition is ignored** by the engine, because it misfires on the title screen
  (lives read as uninitialized RAM there). The game's states decide game over with `_terminated()`.
- **Game-over and continue screens** change RAM (lives reset, flags flip). Only trust flags inside play.
- **`RamInfo.position()`, `RamInfo.remaining_lives()` and `RamInfo.dynamics()` are methods** the engine calls
  every frame; override them as methods, never as a property or field. Run
  `python -m datenwissenschaften.tas.run verify` on a movie before shipping, so an interface mismatch fails
  locally.

## 3. Develop the state machine yourself

Derive the states from the gates, not from a template: one state per gate, in the order the game enforces.
The search splits the movie at the state machine's transitions and only aims at states it recognises.

- One state per phase with a single goal: search for X, reach X, operate X, leave through X. Every state sets
  `goal`, one imperative line of at most 60 characters ("Ring the bell on the scale"); the stream shows it.
- Every boundary is a visible game event a viewer can name (item picked up, body grows, door opens, bell
  rings, new screen), read from a verified RAM value, never an unverified threshold or an invisible count.
- `_next()` returns the next state on the verified forward condition, or an earlier state when a precondition
  is lost. The search only keeps crossings into later states and drops backward transitions.
- A crossing only counts when the new state holds for a few seconds of idle play, so a transition that flickers
  back is never kept.
- `_won()` only in the final state, on the verified win flag.
- `_terminated()` only on game over; lost lives are read from `remaining_lives()`.
- The final state must not treat what the exit does to the player as damage (an exit may drain a resource
  to zero).

## 4. Rewards

Inside a segment the search branches half the time from the tenth of cells that earned the most of the state's
reward, so the reward is its sense of direction:

| Signal | Rule |
|---|---|
| Transition to the next state | the largest reward of the state; never for a fallback |
| Approach | potential-based: pixels closer to the state's target pay, pixels away cost the same |
| Progress | only for verified RAM progress (items, counters) |
| Hit | a cost per unit of health, weight or armour lost, except where the game itself drains it |
| Lost life | a large cost |
| Step cost | a small cost per frame, so the faster branch also earns more |

Check each state: no loop can farm reward (approach rewards are refunded when moving away, fallbacks pay
nothing), and damage is compared with the previous frame so a respawn is not charged twice.

## 5. Actions

- `ACTION_TABLE` has shape `(actions, frames, buttons)` in the order of `env.buttons`; 4 frames per decision
  works well. `GameWrapper.current_action_table()` may narrow it per state.
- Hold movement buttons for all frames; tap edge-triggered buttons (fire, jump, attack) on frame 0 only.
- Test whether the action set can pass every obstacle (a tapped jump from standstill lands on the same spot;
  jumping onto ledges may need the direction held).

## 6. How the search uses the package (verify before changing)

- Every movie boots the game at power-on with every button, like a real speedrun: the title screen is the
  first state (a `Menu` state), and every level is a later state of the same run. Never use the bundled
  stable-retro states (`Level1.state`).
- Each segment is searched Go-Explore style from the previous segment's savestate: cells keyed by state,
  8 px position, height, airborne and `dynamics()`, random input bursts of the action table, the state's reward
  and the route memory (`<paths.models>/<game>/<State>/route.json`) as guides. Deaths (`remaining_lives()`)
  and backward transitions end a branch.
- After every segment the whole movie replays from power-on; a segment that does not reproduce is searched
  again. A segment without a way out is marked stuck in `cache/tas/stuck.json`, which starts a lab run.
- `GameWrapper.levels` groups the states into levels for the stream's level splits.

## 7. Diagnose a run

Read `<upload.url>/live/snapshot?api_key=$STREAM_API_KEY` (`metadata.speedrun`: time, segments, splits, the
state being searched and `stuck`), `/app/working/cache/tas/search.log`, and `/live/movie.mp4`
(the whole verified run from power-on as a video).

| Symptom | Cause | Action |
|---|---|---|
| "No way out of <State>" again and again | the cell key or the reward misses what matters there | add the missing value to `dynamics()` or a reward for progress toward the state's exit |
| The search leaves a state backward or dies at one place | an undetected hazard or enemy | find it in the frames, read it from RAM, and charge touching it |
| A segment is found but does not replay | the transition fires on a value that differs between runs | read the transition from a verified, stable RAM value |
| Branches end without a death on screen | `remaining_lives()` drops without a death | find the true lives byte on frames; return `None` outside play |
| Crossings flicker back into the previous state | the boundary is not a stable game event | move the boundary to a visible, lasting event |
| A level without progress in the movie | the level has no states yet | research its route and add its states with verified transitions |
| The movie is slower than the records | the route takes the long way | follow the records' route and skips where the category allows them |
| The same blocker gets a different kind of change every run | no run scores the previous one | score the open ledger entry first; one hypothesis at a time |

## 8. Deploy

- The image is built from the package plus the committed engine (`dokku/deploy.sh`). When working against a
  local engine checkout, commit it first; never commit `config.yaml` with API keys or ROMs.
- Every deploy is stamped with a CalVer release `YYYY.MM.DD-N` written into `ui.release`. The stream shows it
  and reloads itself when it changes.
- Keep the build cache: a scheduled `docker builder prune -af` makes the next deploy rebuild every layer.
  Prune only by age (`docker builder prune -f --filter until=168h`) or by hand.
- A push that is interrupted locally can keep building on the server: make sure the old build is gone
  before pushing again.
- Deploying restarts the search from the level routes in `cache/tas/levels.msgpack` and the full run in
  `cache/tas/progress.msgpack`.

## 9. Scheduled autonomous runs on the server

The server runs the `speedrun` workflow around the clock as a Dokku app: the engine's search writes and improves
the fastest movie from power-on (`datenwissenschaften.tas`, its data in `/app/working/cache/tas/`). Every
`agent.schedule` Dokku's scheduler (a `cron` entry in `app.json`, generated by `dokku/deploy.sh`) runs the Flyte
task `lab`, which starts a lab run at once when the search is stuck, or when the movie made no progress for
`agent.stall_minutes` minutes. A lab run (`agent/daily.sh`, prompt in `agent/PROMPT.md`) gives Claude Code
`agent.minutes` minutes on its own git worktree (`<package>-claude`, branch `lab/<start>/claude`). The branch is
merged and deployed only when it has commits, `pytest` passes and the current movie still replays from power-on
with it (`python -m datenwissenschaften.tas.run verify`). The repositories are mounted into the container at
`/workspace`; Claude's token lives in the app's Dokku config (`CLAUDE_CODE_OAUTH_TOKEN`). Every deploy and
schedule value comes from `config.yaml`. The steps of a run are in `agent/PROMPT.md`. The session is the lead: it
delegates to the subagents in `.claude/agents/` (scout, researcher, engineer, verifier). A run with work the
verifier has not passed when the time is up gets one extension of `agent.extension_minutes` to finish it. When no
lab run is due and five new reports landed in `agent/reports/`, the critic (`agent/critic.sh`, `agent/CRITIC.md`,
read-only, 3 minutes) writes at most five lessons to `agent/LESSONS.md`, which every lead reads first.
