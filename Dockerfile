# Build instructions: see https://rye.astral.sh/guide/docker/

FROM python:3.12.3-alpine

RUN --mount=source=dist,target=/dist PYTHONDONTWRITEBYTECODE=1 pip install --no-cache-dir /dist/*.whl

LABEL org.opencontainers.image.authors="Jennings Zhang <Jennings.Zhang@childrens.harvard.edu>, FNNDSC <dev@babyMRI.org>" \
      org.opencontainers.image.title="ChRISomatic" \
      org.opencontainers.image.description="ChRIS backend administration tool" \
      org.opencontainers.image.url="https://chrisproject.org/" \
      org.opencontainers.image.source="https://github.com/FNNDSC/chrisomatic" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /
CMD ["chrisomatic"]
