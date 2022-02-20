from serde import deserialize
from chris.common.types import (
    ApiUrl, PluginName, ImageTag, PluginVersion,
    ChrisUsername
)
from chris.common.atypes import AbstractCollectionLinks, AbstractNewUser
from chris.store.types import PluginId, PluginUrl, PluginSearchUrl, UserId, UserUrl
from typing import Optional


@deserialize
class NewStoreUser(AbstractNewUser):
    url: UserUrl
    id: UserId
    username: ChrisUsername
    email: str
    favorite_plugin_metas: ApiUrl
    collab_plugin_metas: ApiUrl


@deserialize
class AnonymousCollectionLinks(AbstractCollectionLinks):
    plugin_stars: ApiUrl
    plugins: ApiUrl
    pipelines: ApiUrl


@deserialize
class StoreCollectionLinks(AnonymousCollectionLinks):
    pass


@deserialize
class AnonymousHome:
    collection_links: AnonymousCollectionLinks


@deserialize
class PluginUpload:
    url: PluginUrl
    id: PluginId


# {
#     "url": "http://localhost:8010/api/v1/plugins/1/",
#     "id": 1,
#     "creation_date": "2022-02-19T13:48:32.099324-05:00",
#     "name": "pl-copy",
#     "version": "1.0.0",
#     "dock_image": "localhost/fnndsc/pl-copy:1.0.0",
#     "public_repo": "https://github.com/FNNDSC",
#     "icon": "",
#     "type": "ds",
#     "stars": 0,
#     "authors": "FNNDSC <dev@babyMRI.org>",
#     "title": "simple-copy",
#     "category": "",
#     "description": "A ChRIS ds plugin that copies data",
#     "documentation": "https://github.com/FNNDSC/chris_plugin/tree/master/examples/pl-copy",
#     "license": "MIT",
#     "execshell": "/usr/local/bin/python",
#     "selfpath": "/usr/local/bin",
#     "selfexec": "simple_copy",
#     "min_number_of_workers": 1,
#     "max_number_of_workers": 1,
#     "min_cpu_limit": 1000,
#     "max_cpu_limit": 2147483647,
#     "min_memory_limit": 200,
#     "max_memory_limit": 2147483647,
#     "min_gpu_limit": 0,
#     "max_gpu_limit": 0,
#     "parameters": "http://localhost:8010/api/v1/plugins/1/parameters/",
#     "meta": "http://localhost:8010/api/v1/1/"
# }


@deserialize
class Plugin:
    url: PluginUrl
    id: PluginId
    name: PluginName
    dock_image: ImageTag
    version: PluginVersion


# I wonder if this can be generic?
@deserialize
class PluginSearch:
    count: int
    next: Optional[PluginSearchUrl]
    previous: Optional[PluginSearchUrl]
    results: list[Plugin]


# {
#     "count": 1,
#     "next": null,
#     "previous": null,
#     "results": [
#         {
#             "url": "https://chrisstore.co/api/v1/plugins/124/",
#             "id": 124,
#             "creation_date": "2022-01-14T10:59:52.034082-05:00",
#             "name": "pl-smoothness-error",
#             "version": "1.0.0",
#             "dock_image": "fnndsc/pl-smoothness-error:1.0.0",
#             "public_repo": "https://github.com/FNNDSC/pl-smoothness-error",
#             "icon": "",
#             "type": "ds",
#             "stars": 0,
#             "authors": "Jennings Zhang <Jennings.Zhang@childrens.harvard.edu>",
#             "title": "Surface Mesh Smoothness Error",
#             "category": "Surface Analysis",
#             "description": "Calculate vertex-wise smoothness error of a .obj surface mesh",
#             "documentation": "https://github.com/FNNDSC/pl-smoothness-error",
#             "license": "MIT",
#             "execshell": "/opt/conda/bin/python",
#             "selfpath": "/opt/conda/bin",
#             "selfexec": "smoothness_error",
#             "min_number_of_workers": 1,
#             "max_number_of_workers": 1,
#             "min_cpu_limit": 1000,
#             "max_cpu_limit": 2147483647,
#             "min_memory_limit": 200,
#             "max_memory_limit": 2147483647,
#             "min_gpu_limit": 0,
#             "max_gpu_limit": 0,
#             "parameters": "https://chrisstore.co/api/v1/plugins/124/parameters/",
#             "meta": "https://chrisstore.co/api/v1/72/"
#         }
#     ]
# }
