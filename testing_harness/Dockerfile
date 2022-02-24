FROM ghcr.io/fnndsc/python-poetry:1.1.13

WORKDIR /usr/local/src/chrisomatic

COPY poetry.lock .
COPY pyproject.toml .
RUN poetry install --no-root

CMD ["python", "-m", "chrisomatic.cli.noop"]
