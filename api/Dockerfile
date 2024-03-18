ARG BASE_IMAGE="python:3.11.8-alpine3.19@sha256:65cb2034c64b4519f1481c552a30ae3fe19f47f3610513b0387dc2e1570080fa"
FROM ${BASE_IMAGE} as builder

ARG RIE_VERSION="v1.9"

RUN apk add --no-cache \
    autoconf \
    automake \
    build-base \
    gcc \
    libc-dev \
    libcurl \
    libstdc++ \
    libtool \
    make \
    cmake \
    python3-dev \
    wget

# Install libexecinfo-dev from the Alpine v3.16 repository
RUN apk add --no-cache --update --repository=https://dl-cdn.alpinelinux.org/alpine/v3.16/main/ \
    libexecinfo-dev

RUN wget https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/download/${RIE_VERSION}/aws-lambda-rie

RUN mkdir -p /pymodules \
    && pip install awslambdaric --target /pymodules

COPY ./requirements.txt /
RUN pip install -r /requirements.txt --target /pymodules

# Lambda API image
FROM ${BASE_IMAGE} as lambda

COPY --from=builder /pymodules /pymodules
COPY --from=builder /aws-lambda-rie /usr/bin/aws-lambda-rie

# Build variables
ARG FUNCTION_DIR="/function"
ARG GIT_SHA
ENV GIT_SHA=$GIT_SHA
ENV PYTHONPATH=/pymodules

RUN apk upgrade --no-cache \
    && apk add --no-cache \
    aws-cli \
    clamav \
    binutils \
    libstdc++

COPY bin/entry.sh /
RUN chmod 555 /usr/bin/aws-lambda-rie /entry.sh

# Setup ClamAV config
COPY conf /etc/clamav
RUN mkdir -p /tmp/clamav/quarantine \
    && chown -R clamav:clamav /tmp/clamav \
    && chown -R clamav:clamav /etc/clamav

# Copy function code
WORKDIR ${FUNCTION_DIR}
COPY . ${FUNCTION_DIR}

ENTRYPOINT [ "/entry.sh", "main.handler" ]