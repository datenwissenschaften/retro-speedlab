# Retro Speedlab Cookiecutter

Start a retro reinforcement-learning project without rebuilding the boring parts.

This Cookiecutter template generates a ready-to-hack training workspace for retro game AI experiments using:

* Stable Retro
* Gymnasium
* Stable-Baselines3 PPO
* Poetry
* Black
* Ruff
* Project metadata via `pyproject.toml`

The goal is simple:

**Spend less time setting up infrastructure and more time training agents, shaping rewards, inspecting RAM, and competing on Retro Speedlab.**

---

## Quick Start

Install Cookiecutter:

```bash
pipx install cookiecutter
```

Generate a new retro RL project:

```bash
cookiecutter https://github.com/datenwissenschaften/retro-speedlab
```

Enter the generated project:

```bash
cd your-project-name
```

Create your local environment file:

```bash
cp .env.example .env
```

Install dependencies:

```bash
poetry install
```

Run training:

```bash
poetry run python app.py
```

---

## Why This Exists

Every retro reinforcement-learning project starts with excitement.

You pick a game.
You define a reward function.
You imagine the agent discovering faster routes than humans would try.

Then reality hits.

Before training a single frame, you rebuild the same setup again:

* Stable Retro integration
* Gymnasium wrappers
* observation preprocessing
* PPO defaults
* project metadata
* formatting tools
* environment configuration

This template packages those repetitive decisions so each new project starts from a clean, reproducible foundation.

The generated project is intentionally small. It is meant to be forked, modified, extended, and argued with.

---

## Generated Project Structure

A generated project looks like this:

```text
your-project/
├── app.py
├── .env.example
├── pyproject.toml
├── .pre-commit-config.yaml
├── game/
│   ├── __init__.py
│   └── environment.py
└── model/
    ├── __init__.py
    └── ppo.py
```

### `app.py`

Main training entry point.

This is where the environment and model are connected.

### `game/`

Game-specific logic.

Use this folder for:

* Gymnasium wrapper code
* reward shaping
* RAM inspection
* termination conditions
* observation preprocessing
* game-state extraction

### `model/`

Model construction logic.

The default setup provides a Stable-Baselines3 PPO factory that can be changed as your experiment evolves.

### `.env.example`

Local runtime configuration.

This includes expected settings such as the API key for Retro Speedlab.

### `pyproject.toml`

Project metadata and dependency configuration rendered from your Cookiecutter answers.

### `.pre-commit-config.yaml`

Formatting and quality hooks using Black and Ruff.

---

## What You Should Customize

The generated project is only a starting point.

The interesting work happens here:

* choosing the game and state
* defining rewards
* reading RAM values
* designing termination conditions
* tuning PPO parameters
* testing different observation spaces
* recording videos
* publishing benchmark results

Good retro RL projects make their assumptions visible.

When publishing your project, document:

* ROM/game version
* emulator state
* reward function
* RAM addresses
* model changes
* training budget
* videos or score curves
* failed experiments

Failed runs with clear notes are useful too.

---

## Retro Speedlab

This template is part of the Retro Speedlab ecosystem.

Retro Speedlab is a platform for benchmarking AI speedrunners in retro games.

The long-term goal is to make retro reinforcement-learning experiments:

* easier to reproduce
* easier to compare
* easier to publish
* easier to compete with

Website:

```text
https://speedlab.datenwissenschaften.com/
```

---

## ROMs

Generated projects use Stable Retro to interface with classic games.

You must provide your own legally obtained ROMs.

This project does not include ROMs and does not encourage piracy.

Only use ROMs in a way that is correct under applicable law.

Refer to the Stable Retro documentation for importing and configuring games.

---

## Template Variables

Cookiecutter asks for values such as:

| Variable             | Purpose                                   |
| -------------------- | ----------------------------------------- |
| `project_name`       | Human-readable project name               |
| `project_slug`       | Package/distribution slug                 |
| `version`            | Initial project version                   |
| `description`        | Project summary                           |
| `author_name`        | Author name                               |
| `author_email`       | Author email                              |
| `license`            | SPDX license expression                   |
| `python_requires`    | Python version range                      |
| `python_classifier`  | Python classifier version                 |
| `python_target`      | Black/Ruff target, for example `py312`    |
| `development_status` | PyPI development-status classifier suffix |

These values are rendered into the generated `pyproject.toml`.

---

## Example Workflow

A typical workflow looks like this:

```bash
cookiecutter https://github.com/datenwissenschaften/retro-speedlab

cd my-retro-agent

cp .env.example .env

poetry install

poetry run python app.py
```

Then iterate on:

```text
game/environment.py
model/ppo.py
app.py
```

---

## Community Workflow

Retro Speedlab is meant for competitive and reproducible AI speedrunning experiments.

When sharing a project generated from this template, consider including:

* the game and category
* training budget
* reward design
* final progress
* best time
* video evidence
* model configuration
* relevant RAM addresses
* notes on failed strategies

Small, readable projects are useful.

Clear failed experiments are useful.

Benchmarks become meaningful only when the setup is visible.

---

## Related Links

Retro Speedlab:

```text
https://speedlab.datenwissenschaften.com/
```

Medium article:

```text
https://medium.com/@datenwissenschaften/retro-reinforcement-learning-cookiecutter-e3aa22b258dd
```

Benchmarking article:

```text
https://medium.com/@datenwissenschaften/benchmarking-ai-speedrunners-78fab55700eb
```

---

## License

Generated projects default to `GPL-3.0-only`, but you can choose a different SPDX license expression during project generation.

Check the generated project’s `pyproject.toml` for the selected license.
