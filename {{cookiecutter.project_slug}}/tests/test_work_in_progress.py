import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "agent" / "work_in_progress.sh"


def git(worktree: Path, *arguments: str) -> str:
    command = ["git", "-C", str(worktree), "-c", "user.name=lab", "-c", "user.email=lab@example.com", *arguments]
    return subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip()


def in_progress(worktree: Path, base: str) -> bool:
    command = f'source "{SCRIPT.as_posix()}" && work_in_progress "{worktree.as_posix()}" {base}'
    return subprocess.run(["bash", "-c", command], check=False).returncode == 0


def commit(worktree: Path, path: str, text: str) -> None:
    (worktree / path).parent.mkdir(parents=True, exist_ok=True)
    (worktree / path).write_text(text, encoding="utf-8")
    git(worktree, "add", path)
    git(worktree, "commit", "--quiet", "-m", path)


def test_only_unverified_work_outside_agent_earns_the_extension(tmp_path: Path):
    git(tmp_path, "init", "--quiet")
    commit(tmp_path, "src/play.py", "one\n")
    base = git(tmp_path, "rev-parse", "HEAD")

    assert not in_progress(tmp_path, base)
    commit(tmp_path, "agent/reports/now.md", "report\n")
    assert not in_progress(tmp_path, base)
    commit(tmp_path, "src/play.py", "two\n")
    assert in_progress(tmp_path, base)
    (tmp_path / "agent" / ".verified").write_text(git(tmp_path, "rev-parse", "HEAD"), encoding="utf-8")
    assert not in_progress(tmp_path, base)
    (tmp_path / "src" / "play.py").write_text("three\n", encoding="utf-8")
    assert in_progress(tmp_path, base)
