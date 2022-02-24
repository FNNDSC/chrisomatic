#!/bin/bash

if [ "$program" = 'try' ]; then
  set -ex
  export PYTHONPATH=$PWD:$PYTHONPATH
  exec /testing_harness/create_example.py | python -m chrisomatic.cli -
else
  set -ex
  exec pytest --color=yes --code-highlight=yes -o cache_dir=/var/cache/pytest
fi
