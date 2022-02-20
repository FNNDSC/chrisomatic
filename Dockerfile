FROM python:3.10.2-alpine

WORKDIR /usr/local/src/chrisstore-client
COPY chris-client .
RUN pip install -r requirements.txt && pip install .

COPY org /usr/share/ansible/plugins/modules
