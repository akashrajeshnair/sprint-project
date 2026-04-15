"""Run the test suite in a deterministic order.

This script runs each pytest test module sequentially and prints a
PASS/FAIL summary per file, plus an overall summary.

Usage (from repo root):
    .venv/Scripts/python.exe tests/run_all_tests.py

Optional:
    .venv/Scripts/python.exe tests/run_all_tests.py -q
    .venv/Scripts/python.exe tests/run_all_tests.py -vv
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _default_test_order(unit_dir: Path) -> list[Path]:
    preferred = [
        unit_dir / "test_rag_tool.py",
        unit_dir / "test_web_search_tool.py",
        unit_dir / "test_score_tool.py",
        unit_dir / "test_explanation_tool.py",
        unit_dir / "test_comparison_tool.py",
    ]

    discovered = sorted(unit_dir.glob("test_*.py"))
    seen: set[Path] = set()

    ordered: list[Path] = []
    for item in preferred:
        if item.exists() and item not in seen:
            ordered.append(item)
            seen.add(item)

    for item in discovered:
        if item not in seen:
            ordered.append(item)
            seen.add(item)

    return ordered


def _run_one(pytest_args: list[str], test_path: Path, repo_root: Path) -> int:
    cmd = [sys.executable, "-m", "pytest", str(test_path), *pytest_args]
    print(f"\n=== Running: {test_path.as_posix()} ===")
    result = subprocess.run(cmd, cwd=str(repo_root))
    if result.returncode == 0:
        print(f"PASS: {test_path.name}")
    else:
        print(f"FAIL: {test_path.name} (exit code {result.returncode})")
    return int(result.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(add_help=True, allow_abbrev=False)
    parser.add_argument(
        "pytest_args",
        nargs="*",
        help="Extra args passed to pytest.",
    )
    args, unknown = parser.parse_known_args()
    pytest_args: list[str] = list(args.pytest_args) + list(unknown)

    tests_dir = Path(__file__).resolve().parent
    repo_root = tests_dir.parent
    unit_dir = tests_dir / "unit"

    test_files = _default_test_order(unit_dir)
    if not test_files:
        print("No tests found under tests/unit (expected files named test_*.py).")
        return 2

    failures: list[Path] = []
    for test_file in test_files:
        code = _run_one(pytest_args, test_file, repo_root=repo_root)
        if code != 0:
            failures.append(test_file)

    print("\n=== Summary ===")
    print(f"Total files: {len(test_files)}")
    print(f"Passed: {len(test_files) - len(failures)}")
    print(f"Failed: {len(failures)}")
    for failed in failures:
        print(f"- {failed.as_posix()}")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
