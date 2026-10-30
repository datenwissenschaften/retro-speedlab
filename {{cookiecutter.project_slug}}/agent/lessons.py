import json
import re
from datetime import UTC, datetime
from pathlib import Path

import typer
from loguru import logger

MAX_LESSONS = 5
MAX_CHARACTERS = 100
PRINTABLE = re.compile(r"[\x20-\x7e]+")


def checked(lessons: list[str]) -> list[str]:
    if len(lessons) > MAX_LESSONS:
        raise ValueError(f"The critic wrote {len(lessons)} lessons, at most {MAX_LESSONS} are allowed")
    for lesson in lessons:
        if len(lesson) > MAX_CHARACTERS or not PRINTABLE.fullmatch(lesson):
            raise ValueError(f"The lesson {lesson!r} is not one printable line of at most {MAX_CHARACTERS} characters")
    return lessons


def main(answer: Path, critic: Path, notes: Path, runs: int) -> None:
    lessons = checked(json.loads(answer.read_text(encoding="utf-8"))["structured_output"]["lessons"])
    at = datetime.now(UTC).isoformat(timespec="seconds")
    critic.write_text(json.dumps({"at": at, "runs": runs, "lessons": lessons}), encoding="utf-8")
    lines = [f"- {lesson}" for lesson in lessons]
    header = f"# Lessons\n\nThe critic's review of the last {runs} lab reports at {at}. Read them before planning.\n"
    notes.write_text("\n".join([header, *lines, ""]), encoding="utf-8")
    logger.info(f"The critic wrote {len(lessons)} lessons from {runs} lab reports")


if __name__ == "__main__":
    typer.run(main)
