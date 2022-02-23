# syntax=docker/dockerfile:1
FROM ubuntu:18.04
COPY . /SDDGen

## Setup Environment
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV FLASK_APP=main.py
EXPOSE 5000

## Get Python3
RUN apt update
RUN apt install -y python3
RUN apt install -y python3-pip


## Instal python requirements
RUN pip3 install -r SDDGen/requirements.txt
RUN mkdir -p /root/nltk_data/tokenizers
RUN mv /SDDGen/lib/punkt /root/nltk_data/tokenizers/punkt

## Run Server on local host
##CMD cd SDDGen; flask run --host=0.0.0.0
