# _ChRISomatic_

[//]: # ([![Version]&#40;https://img.shields.io/docker/v/fnndsc/chrisomatic?sort=semver&#41;]&#40;https://hub.docker.com/r/fnndsc/chrisomatic&#41;)

[![MIT License](https://img.shields.io/github/license/fnndsc/chrisomatic)](https://github.com/FNNDSC/chrisomatic/blob/master/LICENSE)

[//]: # ([![Build]&#40;https://github.com/FNNDSC/chrisomatic/actions/workflows/ci.yml/badge.svg&#41;]&#40;https://github.com/FNNDSC/chrisomatic/actions&#41;)

`chrisomatic` is a tool for automatic administration of _ChRIS_ backends.
It is particularly useful for seeding a setup for testing or development,
though it may also (work and) be useful for deployments.

## Features

- [rich](https://pypi.org/project/rich/) CLI output
- asynchronous tasks (speed!)

## Usage

There are two steps: create a configuration file, then apply it with
the command `chrisomatic apply`.

### Configuration File

A subset of a _ChRIS_ backend's state (users, plugins, pipelines, compute
environments) can be described statically by the _ChRISomatic_ spec.

First, create a configuration file called `chrisomatic.yml`.
This file describes your _ChRIS_ system and what to add to it.

Here is an example which reflects a minimal working _CUBE_:

```yaml
on:
  cube_url: http://localhost:8000/api/v1/
  chris_superuser:
    username: chris
    password: chris1234

cube:
  computeresources:
    - name: host
      url: http://localhost:5005/api/v1/
  plugins:
    - pl-dircopy
    - pl-tsdircopy
    - pl-topologicalcopy
```

#### Plugins and Pipelines

The most common use case for `chrisomatic` is to automatically
register plugins to _ChRIS_. Plugins can be specified by any of:

- ChRIS store URL, e.g. `https://chrisstore.co/api/v1/plugins/108/`
- name, e.g. `pl-dircopy`
- container image, e.g. `ghcr.io/fnndsc/pl-dircopy:2.1.1` 
- source code repository, e.g. `https://github.com/FNNDSC/pl-dircopy`

If the plugin can be found in either the targeted _CUBE_'s paired
_ChRIS_ store or a public _ChRIS_ store (default: https://chrisstore.co/),
then it is registered.

If the plugin cannot be found in any known _ChRIS_ store, then
`chrisomatic` will attempt to produce the plugin JSON representation,
upload it to the configured _ChRIS_ store backend, and then register
it to the targeted _CUBE_. `chrisomatic` supports this operation for
conventional plugins with either can be described by 
[`chris_plugin_info`](https://github.com/FNNDSC/chris_plugin)
or were created from
[`cookiecutter-chrisapp`](https://github.com/fnndsc/cookiecutter-chrisapp).

##### Advanced

Read the complete spec: [docs/SPEC.adoc](docs/SPEC.adoc)

By default, plugins are registered to every compute environment listed.
This behavior can be changed by specifying plugins in object form:

```yaml
cube:
  plugins:
    - name: pl-fastsurfer_inference
      compute_resource:
        - host
        - moc
```

### Running `chrisomatic`

`chrisomatic` should be used as a container.

```shell
TODO TODO TODO
```

#### What Happens?

1. Wait for CUBE to be ready to accept connections
2. Check if superuser exists. If not:
   1. Attempt to identify container on host running _CUBE_
   2. Attempt to create superuser using Django shell
3. Create normal user accounts.
4. Upload plugins to _ChRIS_.
5. Upload pipelines to _ChRIS_.

## Project Status

Okay, everything above was a lie. Most of these features are not supported yet.
