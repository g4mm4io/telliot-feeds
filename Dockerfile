FROM python:3.9-alpine

#install dependencies for build pip packages
RUN apk add protobuf gcc libc-dev linux-headers nano

#copy and install dependencies for telliot core
WORKDIR /usr/src/app/telliot-core
COPY ./telliot-core .
RUN pip install -e .
RUN pip install -r requirements-dev.txt

#copy and install dependencies for telliot core
WORKDIR /usr/src/app/telliot-feeds
COPY ./telliot-feeds .
RUN pip install -e .
RUN pip install -r requirements.txt
