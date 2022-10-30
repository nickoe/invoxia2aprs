# syntax=docker/dockerfile:1

# Test with:
# docker build -t invoxia2aprs . && docker run --rm invoxia2aprs
#
# Possibly run with:
# docker run  -d --restart always --name invoxia2aprs invoxia2aprs:latest

FROM python:3.10-slim-buster
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
CMD ["python3", "main.py"]

