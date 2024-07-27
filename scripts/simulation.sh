#!/bin/sh -ex
export PYTHONPATH=$PWD
/app/scripts/create_example.py "$@" | python -m chrisomatic.cli -
