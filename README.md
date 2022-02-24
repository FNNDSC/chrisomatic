# _ChRISomatic_

[//]: # ([![Version]&#40;https://img.shields.io/docker/v/fnndsc/chrisomatic?sort=semver&#41;]&#40;https://hub.docker.com/r/fnndsc/chrisomatic&#41;)

[![MIT License](https://img.shields.io/github/license/fnndsc/chrisomatic)](https://github.com/FNNDSC/chrisomatic/blob/master/LICENSE)

[//]: # ([![Build]&#40;https://github.com/FNNDSC/chrisomatic/actions/workflows/ci.yml/badge.svg&#41;]&#40;https://github.com/FNNDSC/chrisomatic/actions&#41;)

`chrisomatic` is a tool for automatic administration of _ChRIS_ backends.
It is particularly useful for seeding a setup for testing or development,
though it may also (work and) be useful for deployments.

## Advantages

- declarative provisioning
- [rich](https://pypi.org/project/rich/) CLI output
- asynchronous tasks (speed!)

## Usage

There are two steps: create a configuration file, then apply it with
the command `chrisomatic apply`.

### Configuration File

A subset of a _ChRIS_ backend's state (users, plugins, pipelines, compute
environments) can be described statically by the _ChRISomatic_ schema.

First, create a configuration file called `chrisomatic.yml`.
This file describes your _ChRIS_ system and what to add to it.

Here is an example which reflects a minimal working _CUBE_:

```yaml
on:
  cube_url: http://localhost:8000/api/v1/
  chris_store_url: http://localhost:8010/api/v1/
  chris_superuser:
    username: chris
    password: chris1234

chris_store:
   users:
      - username: chrisstoreuser
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

Read the complete [schema](docs/schema.adoc) and how it is [interpreted](docs/interpretation.adoc).

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

## Project Scope

WIP.

### Currently Supported Features

- [x] Create CUBE superuser
- [x] Create CUBE users
- [x] Create _ChRIS_ store users
- [x] Add compute resources to CUBE
- [x] Register plugins from a store to CUBE
- [ ] Register plugin given a docker image to CUBE
- [ ] Add pipelines to CUBE
- [x] very fast

### Maybe Features

Support provisioning of _ChRIS_ store independently?
