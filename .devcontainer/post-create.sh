#!/bin/bash

set -ex

poetry config virtualenvs.in-project true
poetry install
poetry run pre-commit install
