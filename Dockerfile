FROM python:3.14-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml uv.lock /app/

RUN apk --no-cache update \
&& apk --no-cache upgrade \
&& apk --no-cache add \
	build-base \
	freetype-dev \
	jpeg-dev \
	zlib-dev \
	curl \
&& pip install --no-cache-dir uv \
&& uv sync --no-dev --no-install-project # Install only dependencies, not the local project package

COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

COPY ./proyecto /app/proyecto
COPY ./tienda /app/tienda
COPY ./manage.py /app/manage.py


EXPOSE 8000

RUN addgroup -S app \
&& adduser -S app -G app \
&& chown -R app:app /app

USER app

ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
