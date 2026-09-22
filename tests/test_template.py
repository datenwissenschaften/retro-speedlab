"""Tests that exercise the Cookiecutter template itself.

These generate real temporary projects with ``cookiecutter`` and inspect the
output. They do not install the generated project's runtime dependencies
(Stable Retro, PyTorch, the ``datenwissenschaften`` library) — that heavier
install-and-smoke-test pass lives in CI (see ``.github/workflows/ci.yml``)
and exercises the generated project's own ``tests/`` suite, which does
depend on the real library.
"""

from __future__ import annotations

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
    "config.yaml",
    "pyproject.toml",
    "README.md",
    "LICENSE",
    ".gitignore",
    ".pre-commit-config.yaml",
    "roms/.gitkeep",
    "src/__init__.py",
    "src/game/__init__.py",
    "src/game/actions.py",
    "src/game/wrapper.py",
    "src/ram/__init__.py",
    "src/ram/airstriker.py",
    "src/states/__init__.py",
    "src/states/survive.py",
    "tests/__init__.py",
    "tests/_helpers.py",
    "tests/test_actions.py",
    "tests/test_ram_airstriker.py",
    "tests/test_survive_state.py",
]

# Directories that must never appear in a generated project: local editor,
# AI-assistant, and build-cache state that lives only on a developer's
# machine and must not leak into template output.
FORBIDDEN_DIRS = {
    "__pycache__",
    ".ruff_cache",
    ".junie",
    ".agents",
    ".codex",
    ".idea",
    ".git",
}


def _generate(tmp_path: Path, extra_context: dict | None = None) -> Path:
    project_dir = cookiecutter(
        str(REPO_ROOT),
        no_input=True,
        extra_context=extra_context,
        output_dir=str(tmp_path),
    )
    return Path(project_dir)


def test_default_generation_has_expected_structure(tmp_path):
    project_dir = _generate(tmp_path)
    assert project_dir.name == "retro-speedlab"
    for relative_path in EXPECTED_FILES:
        assert (project_dir / relative_path).is_file(), f"missing {relative_path}"


def test_no_developer_cruft_leaks_into_generation(tmp_path):
    project_dir = _generate(tmp_path)
    found = {p.name for p in project_dir.rglob("*") if p.is_dir() and p.name in FORBIDDEN_DIRS}
    assert not found, f"forbidden developer-only directories were generated: {found}"


def test_no_unrendered_jinja_tokens_remain(tmp_path):
    project_dir = _generate(tmp_path)
    offenders = []
    for path in project_dir.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "{{ cookiecutter" in text or "{%" in text or "cookiecutter." in text:
            offenders.append(str(path.relative_to(project_dir)))
    assert not offenders, f"unrendered template tokens found in: {offenders}"


def test_generated_python_files_are_syntactically_valid(tmp_path):
    project_dir = _generate(tmp_path)
    for path in project_dir.rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_pyproject_metadata_matches_custom_context(tmp_path):
    context = {
        "project_name": "My Custom Speedlab Bot",
        "version": "1.2.3",
        "description": "A custom retro training project.",
        "author_name": "Jane Example",
        "author_email": "jane@example.com",
        "license": "MIT",
    }
    project_dir = _generate(tmp_path, extra_context=context)

    assert project_dir.name == "my-custom-speedlab-bot"

    metadata = tomllib.loads((project_dir / "pyproject.toml").read_text(encoding="utf-8"))
    project = metadata["project"]
    assert project["name"] == "my-custom-speedlab-bot"
    assert project["version"] == "1.2.3"
    assert project["description"] == context["description"]
    assert project["license"] == "MIT"
    assert project["authors"][0]["name"] == "Jane Example"
    assert project["authors"][0]["email"] == "jane@example.com"


@pytest.mark.parametrize(
    ("project_name", "expected_slug"),
    [
        ("Retro Speedlab", "retro-speedlab"),
        ("My_Cool Project", "my-cool-project"),
        ("UPPERCASE NAME", "uppercase-name"),
        ("multi   space", "multi---space"),
    ],
)
def test_project_slug_derivation(tmp_path, project_name, expected_slug):
    project_dir = _generate(tmp_path, extra_context={"project_name": project_name})
    assert project_dir.name == expected_slug


def test_config_yaml_paths_are_relative_and_portable(tmp_path):
    project_dir = _generate(tmp_path)
    config = yaml.safe_load((project_dir / "config.yaml").read_text(encoding="utf-8"))

    for key in ("roms", "models", "recordings", "cache"):
        value = config["paths"][key]
        assert not value.startswith("/"), f"paths.{key} must be project-relative, got {value!r}"
        assert not value.startswith("~"), f"paths.{key} must not reference a home directory"
        assert str(tmp_path) not in value

    assert config["upload"]["api_key"] is None
    assert config["training"]["game"] == "Airstriker-Genesis-v0"


def test_pre_commit_hooks_are_pinned_to_immutable_refs(tmp_path):
    project_dir = _generate(tmp_path)
    pre_commit_config = yaml.safe_load((project_dir / ".pre-commit-config.yaml").read_text(encoding="utf-8"))

    moving_refs = {"stable", "master", "main", "HEAD", "latest"}
    repo_urls = set()
    for repo in pre_commit_config["repos"]:
        repo_urls.add(repo["repo"])
        assert repo["rev"] not in moving_refs, f"{repo['repo']} is pinned to a moving ref: {repo['rev']}"

    # Ruff's own formatter replaces Black; both must not be configured together.
    assert "https://github.com/psf/black" not in repo_urls


def test_gitignore_actually_blocks_rom_files(tmp_path):
    project_dir = _generate(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=project_dir, check=True)

    rom_file = project_dir / "roms" / "Sonic The Hedgehog (World).md"
    rom_file.write_bytes(b"\x00")

    result = subprocess.run(
        ["git", "check-ignore", "--quiet", str(rom_file)],
        cwd=project_dir,
        check=False,
    )
    assert result.returncode == 0, "a ROM file placed in roms/ must be ignored by git"

    kept = subprocess.run(
        ["git", "check-ignore", "--quiet", str(project_dir / "roms" / ".gitkeep")],
        cwd=project_dir,
        check=False,
    )
    assert kept.returncode == 1, "roms/.gitkeep must stay tracked, not ignored"


def test_no_absolute_developer_paths_in_generated_text_files(tmp_path):
    project_dir = _generate(tmp_path)
    home = str(Path.home())
    offenders = []
    for path in project_dir.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if home in text or str(REPO_ROOT) in text:
            offenders.append(str(path.relative_to(project_dir)))
    assert not offenders, f"generated files reference the local machine's paths: {offenders}"
