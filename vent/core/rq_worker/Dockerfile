FROM alpine:3.6
MAINTAINER Charlie Lewis <clewis@iqt.org>

RUN apk add --update \
    docker \
    libmagic \
    python \
    py2-pip \
    && rm -rf /var/cache/apk/*

RUN pip install rq==0.8.0
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY *.py /

LABEL vent="" \
      vent.name="rq-worker" \
      vent.groups="core,files"

ENTRYPOINT ["rqworker", "-c", "settings"]