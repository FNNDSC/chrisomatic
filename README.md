# _ChRISomatic_

[![Version](https://img.shields.io/docker/v/fnndsc/chrisomatic?sort=semver)](https://hub.docker.com/r/fnndsc/chrisomatic)
[![MIT License](https://img.shields.io/github/license/fnndsc/chrisomatic)](https://github.com/FNNDSC/chrisomatic/blob/master/LICENSE)
[![Build](https://github.com/FNNDSC/chrisomatic/actions/workflows/build.yml/badge.svg)](https://github.com/FNNDSC/chrisomatic/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

`chrisomatic` is a tool for automatic administration of _ChRIS_ backends.
It is particularly useful for the recreation of setups for testing or development,
though it could also (work and) be useful for deployments.

[//]: # (screen recording)
https://github.com/FNNDSC/chrisomatic/assets/20404439/468626be-0ae2-4a28-8d4d-c011f45fbeb7

## Usage

If you are looking for a zero-config _ChRIS_ distribution using `chrisomatic`,
check out [_miniChRIS_](https://github.com/FNNDSC/miniChRIS-docker).
_miniChRIS_ bundles a `doocker-compose.yml` for running _ChRIS_ backend (CUBE)
services, as well as `chrisomatic` for tooling and a correct `chrisomatic.yml`
configuration file. Refer back here for documentation on how to customize
`chrisomatic.yml` to your liking.

The following instructions are on how to use `chrisomatic` manually
with a CUBE that is already running.
There are two steps: create a configuration file `chrisomatic.yml`, and apply
it by running `chrisomatic apply`.

### Configuration File

A subset of a _ChRIS_ backend's state (users, plugins, pipelines, compute
environments) can be described declaratively by the _ChRISomatic_ schema.

First, create a configuration file called `chrisomatic.yml`.
This file describes your _ChRIS_ system and what to add to it.

#### Examples

In general, the examples below should almost work as-is.
You'll probably need to change `on.cube_url`.

##### Basic Configuration

Here is an example which reflects a minimal working _CUBE_:

```yaml
# chrisomatic.yml
version: 1.2

on:
  cube_url: http://localhost:8000/api/v1/
  chris_superuser:
    username: chris
    password: chris1234

cube:
  compute_resource:
    - name: host
      url: http://localhost:5005/api/v1/
      innetwork: true
  plugins:
    - pl-dircopy
    - pl-tsdircopy
    - pl-topologicalcopy
```

##### Complete Example

Most values are flexible and support union data types.

```yaml
# chrisomatic.yml
version: 1.1

## System information
on:

  ## Backend API URLs
  cube_url: http://localhost:8000/api/v1/

  ## ChRIS admin user, will be created if they do not exist.
  chris_superuser:
    username: chris
    password: chris1234

  ## Public instances of CUBE where to find plugins.
  public_store:
     - https://cube.chrisproject.org/api/v1/
  ## If unspecified, the default is ["https://cube.chrisproject.org/api/v1/"]
  ## Alternatively, plugin search in public instances can be disabled
  ## by giving an empty value:
  # public_store:

cube:
  ## List of ChRIS users to create. Email is optional.
  users:
    - username: lana
      password: dubrovnik
    - username: banu
      password: oxford
  ## List of pfcon deployments to add to CUBE.
  compute_resource:
    - name: host
      url: http://localhost:5005/api/v1/
      username: pfcon
      password: pfcon1234
      description: Local compute environment
      innetwork: true
    - name: moc
      url: https://example.com/api/v1/
      username: fake
      password: fake1234
      description: Dummy compute environment for testing purposes

  ## List of plugins to add to CUBE.
  plugins:
      ## by docker image
    - docker.io/fnndsc/pl-tsdircopy
    - docker.io/fnndsc/pl-topologicalcopy

      ## by CUBE plugin URL
    - https://cube.chrisproject.org/api/v1/plugins/96/

      ## by name
    - pl-dcm2niix

      ## by Github repository URL
    - https://github.com/FNNDSC/pl-office-convert

      ## or, be more specific
    - name: pl-dircopy
      compute_resource:
        - host

    - public_repo: https://github.com/FNNDSC/dbg-nvidia-smi/
      compute_resource:
        - host
        - moc
```

See below: how to specify [Plugins and Pipelines](#plugins-and-pipelines).

### Running `chrisomatic`

`chrisomatic` should be run as a container in the same docker network as
the _ChRIS_ backend (CUBE). The CUBE container **should** have the label
`org.chrisproject.role=ChRIS ultron backEnd`.
`chrisomatic` needs the docker daemon socket `/var/lib/docker.sock`
and a configuration file `chrisomatic.yml`.

Usually, _CUBE_ is created using `docker-compose`.
You should add `chrisoatic` as a service to your `docker-compose.yml`.

```yaml
# docker-compose.yml
version: '3.9'  # note the version requirement!

services:
  chrisomatic:
    container_name: chrisomatic
    image: fnndsc/chrisomatic
    networks:
      - local
    volumes:
      - "./chrisomatic.yml:/chrisomatic.yml:ro"
      - "/var/run/docker.sock:/var/run/docker.sock:rw"
    userns_mode: host
    depends_on:
      - chris
    profiles:  # prevents chrisomatic from running by default
      - tools
  chris:
    container_name: chris
    image: ghcr.io/fnndsc/cube
    ports:
      - "8000:8000"
    networks:
      - local
    env_file: secrets.env
    environment:
      DJANGO_DB_MIGRATE: "on"
      DJANGO_COLLECTSTATIC: "on"
    labels:
      org.chrisproject.role: "ChRIS_ultron_backEnd"

# --snip--

networks:
  local:
```

`chrisomatic` should be started interactively after starting CUBE.
Note that the ["profiles" feature](https://docs.docker.com/compose/profiles/)
and `docker-compose run` command require a recent version of docker-compose.

```shell
docker compose up -d
docker compose run --rm chrisomatic
```

Each time you modify `chrisomatic.yml`, rerun `chrisomatic`.

```shell
docker compose run --rm chrisomatic
```

<details>
<summary>What if my version of docker-compose is not supported?</summary>

Try to update docker-compose, obviously. But assuming you can't,
you can achieve a similar workflow by setting the command for the `chrisomatic`
service to be `sleep 1000000` and start it with

```shell
docker compose exec chrisomatic chrisomatic apply
```

</details>

#### Without Docker

A limited feature set is still provided in case `chrisomatic` does not
have access to a container engine (Docker).

- HTTP-Only features:
  - Create compute resources
  - Register plugins from peer CUBEs
- Docker-required features:
  - Register Python _ChRIS_ plugins not found in any peer CUBEs
    (i.e. when `dock_image` refers to a local image)
- Docker-required, same-host features:
  - Create superuser

Docker or Podman is still required to run `chrisomatic` itself.

```shell
podman run --rm -i docker.io/fnndsc/chrisomatic:latest chrisomatic -t - < chrisomatic.yml
```

#### What Happens during `chrisomatic`?

1. Wait for CUBE to be ready to accept connections
2. Check if superuser exists. If not:
   1. Attempt to identify container on host running _CUBE_ (requires Docker)
   2. Attempt to create superuser using Django shell (requires Docker)
3. Add compute resources.
4. Create normal user accounts in _CUBE_.
5. Upload plugins to _ChRIS_. (requires Docker for plugins not found in a peer CUBE)
6. Upload pipelines to _ChRIS_ (not implemented).

#### Plugins and Pipelines

The most common use case for `chrisomatic` is to automatically
register plugins to _ChRIS_. Plugins can be specified by any of:

- Peer CUBE URL, e.g. `https://cube.chrisproject.org/api/v1/plugins/108/`
- name, e.g. `pl-dircopy`
- container image, e.g. `ghcr.io/fnndsc/pl-dircopy:2.1.1` 
- source code repository, e.g. `https://github.com/FNNDSC/pl-dircopy`

If the plugin can be found in a peer instance of CUBE (default: https://cube.chrisproject.org/),
then it is registered.

If the plugin cannot be found in any known _ChRIS_ peer, then
`chrisomatic` will attempt to produce the plugin JSON representation
and register it to CUBE. `chrisomatic` supports this operation for
conventional plugins with either can be described by 
[`chris_plugin_info`](https://github.com/FNNDSC/chris_plugin)
or were created from
[`cookiecutter-chrisapp`](https://github.com/fnndsc/cookiecutter-chrisapp).

##### Advanced

Read the complete [schema](docs/schema.adoc) and how it is [interpreted](docs/interpretation.adoc).

## Development

```shell
# run tests
just test

# run simulation
just sim

# clean up
just nuke
```

### Currently Supported Features

- [x] Create CUBE superuser
- [x] Create CUBE users
- [x] Add compute resources to CUBE
- [x] Register plugin given a docker image to CUBE
- [ ] Add pipelines to CUBE
- [x] very fast
