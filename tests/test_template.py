import ast
import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml
from cookiecutter.main import cookiecutter

REPO_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_FILES = [
    "app.py",
    "config.example.yaml",
    "pyproject.toml",
    "README.md",
    "LICENSE",
    "Dockerfile",
    ".gitignore",
    ".gitattributes",
    ".pre-commit-config.yaml",
    "roms/.gitkeep",
    "integrations/.gitkeep",
    "src/__init__.py",
    "src/game/__init__.py",
    "src/game/actions.py",
    "src/game/wrapper.py",
    "src/ram/__init__.py",
    "src/ram/game.py",
    "src/states/__init__.py",
    "src/states/play.py",
    "tests/__init__.py",
    "tests/test_play.py",
    "tests/test_work_in_progress.py",
    "agent/daily.sh",
    "agent/critic.sh",
    "agent/CRITIC.md",
    "agent/lessons.py",
    "agent/verify.sh",
    "agent/work_in_progress.sh",
    "agent/PROMPT.md",
    "agent/reports/.gitkeep",
    "dokku/deploy.sh",
    "dokku/settings.sh",
    "dokku/setup.sh",
    ".claude/settings.json",
    ".claude/agents/engineer.md",
    ".claude/agents/researcher.md",
    ".claude/agents/scout.md",
    ".claude/agents/verifier.md",
    ".claude/skills/beat-nes-game/SKILL.md",
]

OBSOLETE_PATHS = [
    "config.yaml",
    "probe.py",
    "curriculum",
    "agent/demonstrations",
    "NOTES.md",
    "notes",
    "agent/LESSONS.md",
]

FORBIDDEN_DIRS = {
    "__pycache__",
    ".ruff_cache",
    ".junie",
    ".agents",
    ".codex",
    ".idea",
    ".git",
}

EXECUTABLE_SCRIPTS = ["agent/daily.sh", "agent/critic.sh", "agent/verify.sh", "dokku/deploy.sh", "dokku/setup.sh"]

DEFAULT_CONTEXT: dict[str, str] = {}


def _generate(tmp_path: Path, extra_context: dict[str, str]) -> Path:
    return Path(cookiecutter(str(REPO_ROOT), no_input=True, extra_context=extra_context, output_dir=str(tmp_path)))


def _text_files(project_dir: Path) -> dict[Path, str]:
    texts = {}
    for path in project_dir.rglob("*"):
        if not path.is_file():
            continue
        try:
            texts[path] = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
    return texts


def _config(project_dir: Path) -> dict:
    return yaml.safe_load((project_dir / "config.example.yaml").read_text(encoding="utf-8"))


def _ignored(project_dir: Path, path: Path) -> bool:
    result = subprocess.run(["git", "check-ignore", "--quiet", str(path)], cwd=project_dir, check=False)
    return result.returncode == 0


def test_default_generation_has_expected_structure(tmp_path: Path) -> None:
    project_dir = _generate(tmp_path, DEFAULT_CONTEXT)
    assert project_dir.name == "retro-speedlab-game"
    for relative_path in EXPECTED_FILES:
        assert (project_dir / relative_path).is_file(), f"missing {relative_path}"


def test_obsolete_training_files_are_gone(tmp_path: Path) -> None:
    project_dir = _generate(tmp_path, DEFAULT_CONTEXT)
    found = [path for path in OBSOLETE_PATHS if (project_dir / path).exists()]
    assert not found, f"obsolete paths were generated: {found}"


def test_no_developer_cruft_leaks_into_generation(tmp_path: Path) -> None:
    project_dir = _generate(tmp_path, DEFAULT_CONTEXT)
    found = {p.name for p in project_dir.rglob("*") if p.is_dir() and p.name in FORBIDDEN_DIRS}
    assert not found, f"forbidden developer-only directories were generated: {found}"


def test_no_unrendered_jinja_tokens_remain(tmp_path: Path) -> None:
    project_dir = _generate(tmp_path, DEFAULT_CONTEXT)
    offenders = [
        str(path.relative_to(project_dir))
        for path, text in _text_files(project_dir).items()
        if "{{ cookiecutter" in text or "{%" in text or "cookiecutter." in text
    ]
    assert not offenders, f"unrendered template tokens found in: {offenders}"


def test_generated_python_files_are_syntactically_valid(tmp_path: Path) -> None:
    project_dir = _generate(tmp_path, DEFAULT_CONTEXT)
    for path in project_dir.rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_metadata_and_config_match_custom_context(tmp_path: Path) -> None:
    context = {
        "project_name": "My Custom Speedlab Bot",
        "game": "SuperMarioBros-Nes-v0",
        "game_title": "Super Mario Bros.",
        "author_name": "Jane Example",
        "author_email": "jane@example.com",
    }
    project_dir = _generate(tmp_path, context)

    assert project_dir.name == "my-custom-speedlab-bot"

    project = tomllib.loads((project_dir / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    assert project["name"] == "my-custom-speedlab-bot"
    assert project["description"] == "The fastest run of SuperMarioBros-Nes-v0, searched frame by frame from power-on."
    assert project["license"] == "GPL-3.0-only"
    assert project["authors"][0]["name"] == "Jane Example"
    assert project["authors"][0]["email"] == "jane@example.com"

    config = _config(project_dir)
    assert config["training"]["game"] == "SuperMarioBros-Nes-v0"
    assert config["speedrun"]["id"] == "my-custom-speedlab-bot"
    assert config["speedrun"]["title"] == "Super Mario Bros."
    assert config["dokku"]["app"] == "my-custom-speedlab-bot"
    assert config["agent"]["git_email"] == "jane@example.com"


def test_the_game_title_defaults_to_the_game_name(tmp_path: Path) -> None:
    project_dir = _generate(tmp_path, {"game": "SuperMarioBros-Nes-v0"})
    assert _config(project_dir)["speedrun"]["title"] == "SuperMarioBros"


def test_the_stream_and_the_server_come_from_the_context(tmp_path: Path) -> None:
    context = {
        "twitch_enabled": "false",
        "dokku_host": "dokku-home",
        "dokku_server": "me@dokku-home",
        "dokku_host_address": "198.51.100.7",
        "dokku_workspace_dir": "/home/me/speedlab",
    }
    config = _config(_generate(tmp_path, context))

    assert config["twitch"]["enabled"] is False
    assert config["dokku"]["host"] == "dokku-home"
    assert config["dokku"]["server"] == "me@dokku-home"
    assert config["dokku"]["host_address"] == "198.51.100.7"
    assert config["dokku"]["workspace_dir"] == "/home/me/speedlab"


@pytest.mark.parametrize(
    ("project_name", "expected_slug"),
    [
        ("Retro Speedlab", "retro-speedlab"),
        ("My_Cool Project", "my-cool-project"),
        ("UPPERCASE NAME", "uppercase-name"),
        ("multi   space", "multi---space"),
    ],
)
def test_project_slug_derivation(tmp_path: Path, project_name: str, expected_slug: str) -> None:
    project_dir = _generate(tmp_path, {"project_name": project_name})
    assert project_dir.name == expected_slug


def test_config_paths_are_relative_and_portable(tmp_path: Path) -> None:
    project_dir = _generate(tmp_path, DEFAULT_CONTEXT)
    config = _config(project_dir)

    for key, value in config["paths"].items():
        assert not value.startswith("/"), f"paths.{key} must be project-relative, got {value!r}"
        assert not value.startswith("~"), f"paths.{key} must not reference a home directory"

    assert config["upload"]["api_key"] is None
    assert config["training"]["game"] == "SnakeRattleNRoll-Nes-v0"


def test_the_engine_is_the_sibling_checkout(tmp_path: Path) -> None:
    project_dir = _generate(tmp_path, DEFAULT_CONTEXT)
    metadata = tomllib.loads((project_dir / "pyproject.toml").read_text(encoding="utf-8"))
    engine = metadata["tool"]["poetry"]["dependencies"]["datenwissenschaften"]
    assert engine == {"path": "../retro-speedlab-core", "develop": True}


def test_pre_commit_hooks_are_pinned_to_immutable_refs(tmp_path: Path) -> None:
    project_dir = _generate(tmp_path, DEFAULT_CONTEXT)
    pre_commit_config = yaml.safe_load((project_dir / ".pre-commit-config.yaml").read_text(encoding="utf-8"))

    moving_refs = {"stable", "master", "main", "HEAD", "latest"}
    repo_urls = set()
    for repo in pre_commit_config["repos"]:
        repo_urls.add(repo["repo"])
        assert repo["rev"] not in moving_refs, f"{repo['repo']} is pinned to a moving ref: {repo['rev']}"

    assert "https://github.com/psf/black" not in repo_urls


def test_gitignore_blocks_roms_and_the_secret_config(tmp_path: Path) -> None:
    project_dir = _generate(tmp_path, DEFAULT_CONTEXT)
    subprocess.run(["git", "init", "-q"], cwd=project_dir, check=True)

    rom_file = project_dir / "roms" / "SnakeRattleNRoll-Nes-v0.nes"
    rom_file.write_bytes(b"\x00")
    (project_dir / "config.yaml").write_text("upload: {}\n", encoding="utf-8")

    assert _ignored(project_dir, rom_file), "a ROM file placed in roms/ must be ignored by git"
    assert _ignored(project_dir, project_dir / "config.yaml"), "config.yaml holds keys and must be ignored by git"
    assert not _ignored(project_dir, project_dir / "roms" / ".gitkeep"), "roms/.gitkeep must stay tracked"
    assert not _ignored(project_dir, project_dir / "config.example.yaml"), "config.example.yaml must stay tracked"


def test_no_absolute_developer_paths_in_generated_text_files(tmp_path: Path) -> None:
    project_dir = _generate(tmp_path, DEFAULT_CONTEXT)
    home = str(Path.home())
    offenders = [
        str(path.relative_to(project_dir))
        for path, text in _text_files(project_dir).items()
        if home in text or str(REPO_ROOT) in text
    ]
    assert not offenders, f"generated files reference the local machine's paths: {offenders}"


def test_lab_scripts_are_executable(tmp_path: Path) -> None:
    project_dir = _generate(tmp_path, DEFAULT_CONTEXT)
    for script in EXECUTABLE_SCRIPTS:
        assert (project_dir / script).stat().st_mode & 0o111, f"{script} must be executable"
