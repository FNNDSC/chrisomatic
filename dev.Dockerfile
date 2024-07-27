FROM python:3.12.3-alpine

WORKDIR /app
COPY requirements-dev.lock requirements-dev.lock
RUN --mount=type=cache,sharing=locked,target=/root/.cache/pip \
    sed -i' ' -e '/-e file:\./d' requirements-dev.lock \
    && env PYTHONDONTWRITEBYTECODE=1 pip install -r requirements-dev.lock

CMD ["pytest"]
