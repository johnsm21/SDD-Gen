# syntax=docker/dockerfile:1
FROM ubuntu:18.04
# COPY . /SDDGen

# Copy code and html
COPY ./app /app
COPY ./static /app/static
COPY ./templates /app/templates

# copy dependencies
COPY ./lib /app/lib

# copy server config
COPY ./config.ini /app/config.ini

# setup temp data dir
RUN mkdir /app/temp

## Setup Environment
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV FLASK_APP=main.py
EXPOSE 5000

## Get Python3
RUN apt update
RUN apt install -y python3
RUN apt install -y python3-pip
RUN pip3 install --upgrade pip


## Instal python requirements
RUN pip3 install -r app/lib/requirements.txt --no-cache-dir
RUN mkdir -p /root/nltk_data/tokenizers
RUN mv /app/lib/punkt /root/nltk_data/tokenizers/punkt

## Run Server on local host
WORKDIR /app

# ENTRYPOINT ["python3", "main.py"]
# Example pks12 declaration
ENTRYPOINT ["python3", "main.py", "--cert_name", "mykeystore.pkcs12", "--cert_pass", "password"]
