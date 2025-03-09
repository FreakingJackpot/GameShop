FROM python:3.10-slim-buster

WORKDIR /app

RUN apt-get update
RUN apt-get -y install locales

RUN sed -i 's/^# *\(ru_RU.UTF-8\)/\1/' /etc/locale.gen
RUN locale-gen

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .