FROM docker.io/fnndsc/python-poetry:1.5.1

WORKDIR /usr/local/src/chrisomatic

COPY poetry.lock .
COPY pyproject.toml .
RUN poetry install --no-root

CMD ["pytest", "--color=yes", "--code-highlight=yes", "-o", "cache_dir=/var/cache/pytest"]
