# syntax=docker/dockerfile:1
FROM ubuntu:24.04

## Setup Environment
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
EXPOSE 5000

## Get Python3
RUN apt update
RUN apt install -y python3
RUN apt install -y python3-pip
RUN apt install -y git

## Get the latest code
RUN git clone --depth 1 https://github.com/johnsm21/SDD-Gen.git
# COPY . /SDD-Gen
WORKDIR /SDD-Gen

## Instal python requirements
RUN pip3 install --break-system-packages -r lib/requirements.txt --no-cache-dir
RUN python3 -m nltk.downloader all
RUN python3 downloadModel.py

# RUN mkdir -p /root/nltk_data/tokenizers
# RUN mv /app/lib/punkt /root/nltk_data/tokenizers/punkt

## Run Server on local host
ENTRYPOINT ["python3", "app/main.py"]
# Example pks12 declaration
# ENTRYPOINT ["python3", "app/main.py", "--cert_name", "mykeystore.pkcs12", "--cert_pass", "password"]
