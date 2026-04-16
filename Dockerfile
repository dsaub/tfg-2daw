FROM python:3.14-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN adduser -D -S app

COPY requirements.txt /app/
RUN apk --no-cache update && apk --no-cache upgrade
RUN apk add --no-cache --virtual .build-deps build-base mariadb-dev libffi-dev \
    && apk add --no-cache mariadb-connector-c \
    && pip install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

COPY . /app/
RUN chmod +x /app/entrypoint.sh


EXPOSE 8000
RUN mkdir -pv /fonts
COPY tienda/static/fonts/ /fonts/

RUN chown -R app: /app /fonts
RUN chmod 770 /app/entrypoint.sh
USER app

ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]