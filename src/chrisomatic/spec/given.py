import dataclasses
import re
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property
from typing import Union, Optional, TypeGuard

from aiochris.types import (
    PluginName,
    PluginVersion,
    ImageTag,
    ChrisURL,
    PluginUrl,
    ComputeResourceId,
    ComputeResourceName,
)
from serde import deserialize, serde, Untagged, field, to_dict

from chrisomatic.spec.common import User, ComputeResource, Pipeline


@deserialize
@dataclass(frozen=True)
class On:
    cube_url: ChrisURL
    chris_superuser: User
    public_store: list[ChrisURL]


@dataclass(frozen=True)
class ExpandedBackend:
    users: Sequence[User]
    pipelines: Sequence[Pipeline]


@deserialize
@dataclass(frozen=True)
class GivenBackend:
    users: list[User]
    pipelines: list[Union[str, Pipeline]]

    def expand_pipeline(self, pipeline: str | Pipeline) -> Pipeline:
        if len(self.users) == 0:
            raise ValidationError(f"No users specified for {self.__class__}")
        if isinstance(pipeline, Pipeline):
            return pipeline
        return Pipeline(src=pipeline, owner=self.users[0].username)


@deserialize
@dataclass(frozen=True)
class GivenChrisStore(GivenBackend):
    pass


@serde
@dataclass(frozen=True)
class GivenCubePlugin:
    compute_resource: list[ComputeResourceName] = field(default_factory=list)
    url: Optional[PluginUrl] = None
    name: Optional[PluginName] = None
    version: Optional[PluginVersion] = None
    dock_image: Optional[ImageTag] = None
    public_repo: Optional[str] = None

    @property
    def title(self) -> str:
        if self.name:
            return self.name
        if self.dock_image:
            return self.dock_image
        if self.url:
            return self.url
        if self.public_repo:
            return self.public_repo
        return "Unknown"

    def to_store_search(self) -> dict[str, str]:
        """
        Produce query parameters for a _ChRIS_ store `GET /api/v1/plugins/search/`
        """
        return self.to_search_params()

    def to_cube_search(
        self, compute_resources: dict[ComputeResourceName, ComputeResourceId]
    ) -> Sequence[dict[str, str]]:
        """
        Produce query parameters for a _CUBE_ `GET /api/v1/plugins/search/`
        """
        # public_repo is not searchable
        # https://github.com/FNNDSC/ChRIS_ultron_backEnd/issues/365
        d = self.to_search_params()
        return tuple(
            self.__copy_and_set_compute(d, compute_resources[c])
            for c in self.compute_resource
        )

    @staticmethod
    def __copy_and_set_compute(d: dict, cid: ComputeResourceId) -> dict[str, str]:
        d = d.copy()
        d["compute_resource_id"] = str(cid)
        return d

    def to_search_params(self) -> dict[str, str]:
        d: dict = to_dict(self)
        d["name_exact"] = d["name"]
        del d["name"]
        del d["url"]
        del d["compute_resource"]
        d = {k: v for k, v in d.items() if v is not None}
        return d


@dataclass(frozen=True)
class ExpandedCube(ExpandedBackend):
    compute_resource: Sequence[ComputeResource]
    plugins: Sequence[GivenCubePlugin]


_store_plugin_re = re.compile(r"^https?://.+/api/v1/plugins/\d+/$")


@deserialize(tagging=Untagged)
@dataclass(frozen=True)
class GivenCube(GivenBackend):

    compute_resource: list[ComputeResource]
    plugins: list[Union[str, GivenCubePlugin]]
    pipelines: list

    def expand(self) -> ExpandedCube:
        if len(self.compute_resource) == 0 and len(self.plugins) > 0:
            raise ValidationError(
                "Must specify at least one compute_resource for ChRIS"
            )
        return ExpandedCube(
            users=self.users,
            pipelines=tuple(self.expand_pipeline(p) for p in self.pipelines),
            compute_resource=self.compute_resource,
            plugins=tuple(self.expand_plugin(p) for p in self.plugins),
        )

    def expand_plugin(
        self,
        plugin: str | GivenCubePlugin,
    ) -> GivenCubePlugin:
        resolved_plugin = self.resolve_plugin_type(plugin)
        return self.fill_plugin_compute_resource(resolved_plugin)

    def resolve_plugin_type(self, plugin: str | GivenCubePlugin) -> GivenCubePlugin:
        """
        Ref: docs/interpretation.adoc#plugin_string_resolution
        """
        if isinstance(plugin, GivenCubePlugin):
            return plugin
        if self.looks_like_store_url(plugin):
            return GivenCubePlugin(url=PluginUrl(plugin))
        if self.looks_like_image_tag(plugin):
            return GivenCubePlugin(dock_image=ImageTag(plugin))
        if self.looks_like_public_repo(plugin):
            return GivenCubePlugin(public_repo=plugin)
        return GivenCubePlugin(name=PluginName(plugin))

    def fill_plugin_compute_resource(self, plugin: GivenCubePlugin) -> GivenCubePlugin:
        if len(plugin.compute_resource) == 0:
            return dataclasses.replace(
                plugin, compute_resource=self.compute_resource_names
            )
        self.check_plugin_compute_resources_exist(plugin)
        return plugin

    def check_plugin_compute_resources_exist(self, plugin: GivenCubePlugin) -> None:
        for compute_resource in plugin.compute_resource:
            if compute_resource not in self.compute_resource_names:
                raise ValidationError(
                    f'Error with plugin "{plugin.title}": compute resource '
                    f"not found in {self.compute_resource_names}"
                )

    @cached_property
    def compute_resource_names(self) -> list[ComputeResourceName]:
        return [c.name for c in self.compute_resource]

    @staticmethod
    def looks_like_store_url(s: str) -> TypeGuard[PluginUrl]:
        match = _store_plugin_re.fullmatch(s)
        return match is not None

    @staticmethod
    def looks_like_image_tag(s: str) -> TypeGuard[ImageTag]:
        return (
            s.startswith("docker.io/")
            or s.startswith("ghcr.io/")
            or s.startswith("fnndsc/pl-")
            or (
                s.count(":") == 1
                and s[0].isalpha()
                and s.count("/") <= 2
                and "//" not in s
            )
        )

    @staticmethod
    def looks_like_public_repo(s: str) -> bool:
        return s.startswith("https://github.com/") or s.startswith(
            "https://gitlab.com/"
        )


@dataclass(frozen=True)
class ExpandedConfig:
    version: str
    on: On
    cube: ExpandedCube


@deserialize
@dataclass(frozen=True)
class GivenConfig:
    version: str
    on: On
    cube: GivenCube

    def expand(self) -> ExpandedConfig:
        """
        Fill default values.
        """
        return ExpandedConfig(
            self.version,
            self.on,
            self.cube.expand(),
        )


class ValidationError(Exception):
    pass
