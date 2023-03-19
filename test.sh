#!/usr/bin/env bash

export PYTHONPATH="${PYTHONPATH}:${PWD}"
pipenv run python -m src.main &> python.log