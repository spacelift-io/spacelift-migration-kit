"""Nox sessions."""

import nox
from nox_poetry import Session, session

PYTHON_VERSIONS: list = ["3.10", "3.11", "3.12"]
PYTHON_SOURCES: tuple = "spacemk", "tests", "noxfile.py"

nox.options.sessions = "mypy", "ruff", "tests"


@session(python=PYTHON_VERSIONS)
def mypy(session: Session) -> None:
    """Type-check using mypy."""
    args = session.posargs or PYTHON_SOURCES

    session.install("mypy")
    session.run("mypy", "--ignore-missing-imports", *args)


@session(python=PYTHON_VERSIONS)
def ruff(session: Session) -> None:
    """Lint using ruff."""
    args = session.posargs or []

    session.install("ruff")
    session.run("ruff", "check", "--no-fix", *args)


@session(python=PYTHON_VERSIONS)
def tests(session: Session) -> None:
    """Run the test suite."""
    args = session.posargs or ["--cov", "--durations=10", "--strict-markers"]

    session.run("poetry", "install", external=True)
    session.run("pytest", *args)
