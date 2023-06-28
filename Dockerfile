FROM python:3.9-alpine

#install dependencies for build pip packages
RUN apk add protobuf gcc libc-dev linux-headers nano

#copy and install dependencies for telliot core
WORKDIR /usr/src/app/telliot-core
COPY telliot-core/requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY ./telliot-core .
RUN pip install -e .

#copy and install dependencies for telliot core
WORKDIR /usr/src/app/telliot-feeds
COPY telliot-feeds/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./telliot-feeds .
RUN pip install -e .


