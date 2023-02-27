#!/usr/bin/bash
poetry run pytest -rap --durations=25 tests/test_*.py
