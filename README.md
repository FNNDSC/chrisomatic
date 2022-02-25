# _ChRISomatic_

[![Version](https://img.shields.io/docker/v/fnndsc/chrisomatic?sort=semver)](https://hub.docker.com/r/fnndsc/chrisomatic)
[![MIT License](https://img.shields.io/github/license/fnndsc/chrisomatic)](https://github.com/FNNDSC/chrisomatic/blob/master/LICENSE)
[![Build](https://github.com/FNNDSC/chrisomatic/actions/workflows/build.yml/badge.svg)](https://github.com/FNNDSC/chrisomatic/actions)

`chrisomatic` is a tool for automatic administration of _ChRIS_ backends.
It is particularly useful for seeding a setup for testing or development,
though it could also (work and) be useful for deployments.

![Screen recording](https://ipfs.babymri.org/ipfs/QmXYHhAfgJDvHrAJsAkt77s9UrP4Snz4P7FWTnSayweMcs/chrisomatic.gif)

## Usage

There are two steps: create a configuration file, then apply it with
the command `chrisomatic apply`.

### Configuration File

A subset of a _ChRIS_ backend's state (users, plugins, pipelines, compute
environments) can be described declaratively by the _ChRISomatic_ schema.

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

### Running `chrisomatic`

`chrisomatic` should be run as a container in the same docker network as
the _ChRIS_ backend (CUBE). The CUBE container should have the label
`org.chrisproject.role=ChRIS ultron backEnd`.
`chrisomatic` needs the docker daemon socket `/var/lib/docker.sock`
and a configuration file `chrisomatic.yml`.

```yaml
version: '3.7'

services:
  chrisomatic:
    container_name: chrisomatic
    image: fnndsc/chrisomatic:0.1.0
    networks:
      - local
    volumes:
      - "./chrisomatic.yml:/etc/chrisomatic/chrisomatic.yml:ro"
      - "/var/run/docker.sock:/var/run/docker.sock:rw"
    restart: always
    userns_mode: host
  chris:
    container_name: chris
    image: ghcr.io/fnndsc/chris:3.0.0.pre2
    ports:
      - "8000:8000"
    networks:
      - local
    env_file: secrets.env
    environment:
      DJANGO_DB_MIGRATE: "on"
      DJANGO_COLLECTSTATIC: "on"
    labels:
      org.chrisproject.role: "ChRIS ultron backEnd"

# ...

networks:
  local:
```

The default command for the container `fnndsc/chrisomatic` is to do nothing.
It is recommended to run the command `chrisomatic apply` manually, with
a full-featured TTY console.

Start _ChRIS_ and `chrisomatic` by running:

```shell
docker compose up -d
docker compose exec chrisomatic chrisomatic apply
```

Each time you modify `chrisomatic.yml`, rerun `chrisomatic`.

```shell
docker compose exec chrisomatic chrisomatic apply
```

#### What Happens?

1. Wait for CUBE to be ready to accept connections
2. Check if superuser exists. If not:
   1. Attempt to identify container on host running _CUBE_
   2. Attempt to create superuser using Django shell
3. Add compute resources.
4. Create normal user accounts in both _ChRIS_ store and _CUBE_.
5. Upload plugins to _ChRIS_.
6. Upload pipelines to _ChRIS_ (not implemented).

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

## Errors

Try rerunning it, of course.

`chrisomatic` is highly parallel, which stresses CUBE.
https://github.com/FNNDSC/ChRIS_ultron_backEnd/issues/366

Report bugs: https://github.com/FNNDSC/chrisomatic/issues

## Project Stage and Scope

WIP.

### Currently Supported Features

- [x] Create CUBE superuser
- [x] Create CUBE users
- [x] Create _ChRIS_ store users
- [x] Add compute resources to CUBE
- [x] Register plugins from a store to CUBE
- [x] Register plugin given a docker image to CUBE
- [ ] Add pipelines to CUBE
- [x] very fast

### Maybe Features

Support provisioning of _ChRIS_ store independently?
