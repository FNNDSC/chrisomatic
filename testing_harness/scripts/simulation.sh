#!/bin/bash -ex
export PYTHONPATH=$PWD
/t/create_example.py "$@" | python -m chrisomatic.cli -
