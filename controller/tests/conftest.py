# -*- coding: utf-8 -*-
"""Pytest configuration."""
import sys

import pytest

# don't create .pyc files (Tanner (4/9/23): not sure why this is being done. Also, a .pyc file for conftest.py is still being created)
sys.dont_write_bytecode = True


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--full-ci", action="store_true", default=False, help="include tests that are marked as only for CI"
    )
    parser.addoption(
        "--include-slow-tests", action="store_true", default=False, help="include tests that are a slow"
    )
    parser.addoption(
        "--only-exe",
        action="store_true",
        default=False,
        help="onlyrun tests that are marked for the compiled exe",
    )
    parser.addoption(
        "--live-test",
        action="store_true",
        default=False,
        help="only run tests that are marked for the real (live) instrument",
    )


def pytest_collection_modifyitems(config, items) -> None:
    if config.getoption("--only-exe"):
        skip_non_exe = pytest.mark.skip(
            reason="these tests are skipped when only running tests that only target the compiled .exe file"
        )
        for item in items:
            if "only_exe" not in item.keywords:
                item.add_marker(skip_non_exe)
        return

    skip_exe = pytest.mark.skip(reason="these tests are skipped unless --only-exe option is set")
    for item in items:
        if "only_exe" in item.keywords:
            item.add_marker(skip_exe)

    if not config.getoption("--live-test"):
        skip_live = pytest.mark.skip(reason="these tests are skipped unless --live-test option is set")
        for item in items:
            if "live_test" in item.keywords:
                item.add_marker(skip_live)

    if not config.getoption("--full-ci"):
        skip_ci_only = pytest.mark.skip(reason="these tests are skipped unless --full-ci option is set")
        for item in items:
            if "only_run_in_ci" in item.keywords:
                item.add_marker(skip_ci_only)

    if not config.getoption("--include-slow-tests"):
        skip_slow = pytest.mark.skip(
            reason="these tests are skipped unless --include-slow-tests option is set"
        )
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
