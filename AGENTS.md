# Agent Guide

## Purpose

image-renamer is a Python utility for renaming and organizing image files with tests and a Docker entrypoint.

## Structure

- `rename_images.py`, `organize_files.py`, and `utils.py` contain the core behavior.
- `test_*.py` files cover renaming, organization, and edge cases.
- `Dockerfile` and `entrypoint.sh` support containerized runs.

## Commands

- `pytest` runs the test suite.
- `python rename_images.py --help` inspects rename options.
- `python organize_files.py --help` inspects organization options.

## Guardrails

- Do not commit `.venv/`, `__pycache__/`, `.pytest_cache/`, or user image inputs.
- Preserve filename safety and dry-run style checks before destructive file operations.
- Add regression tests for edge cases involving paths, collisions, or extensions.
