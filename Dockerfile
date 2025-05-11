FROM python:3.13.3-slim

LABEL maintainer="jesus.maciasportela@telefonica.com"
LABEL description="Prometheus GPU VM Gateway Exporter"
LABEL version="0.1"

WORKDIR /app
COPY ./exporter/** /app/

RUN apt-get update && apt-get install -y openssh-client jq && \
    pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
