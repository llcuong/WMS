FROM python:3.6-alpine
MAINTAINER box_chang<forkome@gmail.com>

ENV TZ "Asia/Taipei"

ENV CONFIG_DIR=/config

ENV DJANGO_SETTINGS_MODULE=PMS.settings.test-box-local

RUN apk update && \
 apk add --no-cache --virtual build-deps gcc python-dev musl-dev \
     libuuid \
     pcre \
     mailcap \
     libc-dev \
     linux-headers \
     pcre-dev \
     jpeg-dev \
     zlib-dev \
     freetype-dev \
     lcms2-dev \
     openjpeg-dev \
     tiff-dev \
     tk-dev \
     tcl-dev \
     harfbuzz-dev \
     fribidi-dev \
     mariadb-dev python3-dev && \
 apk add mariadb-client bash


ADD $CONFIG_DIR/app/requirements.txt tmp/

RUN pip install -r tmp/requirements.txt

RUN apk del \
    gcc \
    libc-dev \
    linux-headers \
  && rm -rf /root/.cache /tmp/*

ADD /config /workplace/config

ADD /src /workplace/src
WORKDIR /workplace/src/PMS

#CMD ["gunicorn","/workplace/src/PMS/PMS.wsgi","-c","/workplace/config/gunicorn/gunicorn.py"]
