#!/usr/bin/env python

import sys
import time
from strictyaml import as_document
from chrisomatic.spec.schema import schema
from collections import OrderedDict

if len(sys.argv) >= 2:
    stamp = sys.argv[1]
else:
    stamp = str(int(time.time()))

now = time.asctime()


data = {
    "on": {
        "cube_url": "http://chris:8000/api/v1/",
        "chris_superuser": {"username": f"try-{stamp}", "password": f"trying1234"},
        "public_store": [],
    },
    "cube": {
        "users": [],
        "compute_resource": [],
        "plugins": [
            "docker.io/fnndsc/pl-tsdircopy:1.2.1",
            "ghcr.io/fnndsc/pl-dne:latest",
            "https://cube.chrisproject.org/api/v1/plugins/92/",
            {
                "dock_image": "ghcr.io/fnndsc/pl-unstack-folders:1.0.0",
                "compute_resource": [f"try-{stamp}-cr-b"],
            },
            {
                "name": "pl-dircopy",
                "version": "2.1.1",
                "dock_image": "fnndsc/pl-dircopy",
            },
        ],
    },
}

for letter in "abcdefgh":
    data["cube"]["compute_resource"].append(
        {
            "name": f"try-{stamp}-cr-{letter}",
            "url": f"https://example.com/computeresource/{letter.upper()}/api/v1/",
            "username": f"trycr{letter}",
            "password": "doesntmatter",
            "description": f"trial {letter} created on {now}",
        }
    )
    data["cube"]["users"].append(
        {"username": f"try-{stamp}-{letter * 3}", "password": f"trying1234{letter * 3}"}
    )

yaml = as_document(data, schema=schema)
print(yaml.as_yaml())
