FROM docker.io/fnndsc/python-poetry:1.1.13

WORKDIR /usr/local/src/chrisomatic
COPY . .
RUN poetry install --no-dev

COPY docs/examples/default.yml /etc/chrisomatic/chrisomatic.yml
WORKDIR /etc/chrisomatic
CMD ["chrisomatic", "noop"]
