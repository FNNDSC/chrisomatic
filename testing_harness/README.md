# Local Testing Instructions

This directory provides a setup for testing the client module.

## Setup

```
pushd miniChRIS-docker
docker-compose up -d
popd
```

## Teardown

```shell
pushd miniChRIS-docker
docker-compose down -v
popd
```

## Testing Commands

### Unit Tests

```shell
docker compose run dev
```

### Run Simulation

```shell
docker compose run dev /t/simulation.sh
```
