FROM python:3.7-alpine
MAINTAINER Foodstack Inc.

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /requirements.txt
RUN apk add --update --no-cache postgresql-client jpeg-dev
RUN apk add --update --no-cache --virtual .tmp-build-deps \
      gcc libc-dev linux-headers postgresql-dev musl-dev zlib zlib-dev
RUN pip install -r /requirements.txt
RUN apk del .tmp-build-deps

RUN apk update && \
    apk upgrade && \
    apk add --no-cache libstdc++ && \
    apk add --no-cache --virtual=build_deps g++ gfortran && \
    ln -s /usr/include/locale.h /usr/include/xlocale.h && \
    pip install --no-cache-dir pandas && \
    rm /usr/include/xlocale.h && \
    apk del build_deps

RUN mkdir /app
WORKDIR /app
COPY ./app /app

RUN adduser -D user
USER user
