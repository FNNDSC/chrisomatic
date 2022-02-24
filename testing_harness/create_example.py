#!/usr/bin/env python

import time
from strictyaml import as_document
from chrisomatic.spec.schema import schema
from collections import OrderedDict

stamp = str(int(time.time()))
now = time.asctime()


data = {
    'on': {
        'cube_url': 'http://chris:8000/api/v1/',
        'chris_store_url': 'http://chrisstore.local:8010/api/v1/',
        'chris_superuser': {
            'username': f'try-{stamp}',
            'password': f'trying1234'
        },
        'public_store': [],
    },
    'chris_store': {
        'users': [
            {
                'username': f'try-{stamp}-a',
                'password': f'trying1234a'
            },
            {
                'username': f'try-{stamp}-b',
                'password': f'trying1234b'
            }
        ]
    },
    'cube': {
        'users': [
            {
                'username': f'try-{stamp}-c',
                'password': f'trying1234c'
            },
            {
                'username': f'try-{stamp}-d',
                'password': f'trying1234d'
            },
        ],
        'compute_resource': [
            {
                'name': f'try-{stamp}-cr-a',
                'url': 'http://example.com/',
                'username': 'trycra',
                'password': 'doesntmatter',
                'description': f'trial A created on {now}'
            },
            {
                'name': f'try-{stamp}-cr-b',
                'url': 'http://example.com/',
                'username': 'trycrb',
                'password': 'doesntmatter',
                'description': f'trial B created on {now}'
            },
        ],
        'plugins': [
            'docker.io/fnndsc/pl-tsdircopy:1.2.1',
            'localhost/fnndsc/pl-chrisomatic',
            'https://chrisstore.co/api/v1/plugins/92/',
            {
                'dock_image': 'ghcr.io/fnndsc/pl-nums2mask:1.0.0',
                'compute_resource': [f'try-{stamp}-cr-b']
            }
        ]
    }
}

yaml = as_document(data, schema=schema)
print(yaml.as_yaml())
