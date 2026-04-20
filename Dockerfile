FROM python:3.14-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt /app/
RUN apk --no-cache update && apk --no-cache upgrade
RUN pip install --no-cache-dir -r requirements.txt 

COPY . /app/
RUN chmod +x /app/entrypoint.sh


EXPOSE 8000
RUN mkdir -pv /fonts
COPY tienda/static/fonts/ /fonts/

ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]