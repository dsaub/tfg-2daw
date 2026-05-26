FROM python:3.14-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY pyproject.toml uv.lock /app/ 

RUN apk --no-cache update && apk --no-cache upgrade \
&& pip install --no-cache-dir uv \
&& uv sync --no-dev --no-install-project # Install only dependencies, not the local project package

COPY . /app/
RUN chmod +x /app/entrypoint.sh


EXPOSE 8000
RUN mkdir -pv /fonts
COPY tienda/static/fonts/ /fonts/

ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
