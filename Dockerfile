FROM docker.io/fnndsc/python-poetry:1.1.13

LABEL org.opencontainers.image.authors="Jennings Zhang <Jennings.Zhang@childrens.harvard.edu>, FNNDSC <dev@babyMRI.org>" \
      org.opencontainers.image.title="ChRISomatic" \
      org.opencontainers.image.description="Declarative ChRIS backend administration tool" \
      org.opencontainers.image.url="https://chrisproject.org/" \
      org.opencontainers.image.source="https://github.com/FNNDSC/chrisomatic" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /usr/local/src/chrisomatic
COPY . .
RUN poetry install --no-dev

COPY docs/examples/default.yml /etc/chrisomatic/chrisomatic.yml
WORKDIR /etc/chrisomatic
CMD ["chrisomatic", "apply"]
