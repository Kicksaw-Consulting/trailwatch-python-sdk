#!/bin/bash

poetry run bandit -c pyproject.toml -r src/trailwatch/
