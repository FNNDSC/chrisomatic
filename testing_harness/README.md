# Local Testing Instructions

This directory provides a setup for testing the client module.

## Setup

1. Start [miniChRIS](https://github.com/FNNDSC/miniChRIS)
2. Run `docker compose up -d`

## Teardown

```shell
docker compose down -v --rmi local
```

## Testing Commands

### Unit Tests

```shell
docker compose exec dev /t/pytest
```

### Try with generated data

```shell
docker compose exec dev /t/try
```
