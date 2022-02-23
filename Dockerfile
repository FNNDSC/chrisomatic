FROM ghcr.io/fnndsc/python-poetry:1.1.13

WORKDIR /usr/local/src/chrisomatic
COPY . .
RUN poetry install --no-dev

CMD ["chrisomatic"]
