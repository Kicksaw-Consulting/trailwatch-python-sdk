#!/bin/bash

set -ex

poetry config virtualenvs.in-project true
poetry install --with salesforce
poetry run pre-commit install
