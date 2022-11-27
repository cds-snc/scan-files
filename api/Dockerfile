ARG BASE_IMAGE="python:3.9.15-alpine3.16@sha256:ea679ee27dbb8f36fbfc304be1b488b4fd7bea95dd230a47f97187c2e3fd4807"
FROM ${BASE_IMAGE} as builder

ARG RIE_VERSION="v1.9"

RUN apk add --no-cache \
    autoconf \
    automake \
    build-base \
    gcc \
    libc-dev \
    libcurl \
    libexecinfo-dev \
    libstdc++ \
    libtool \
    make \
    cmake \
    python3-dev \
    wget

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
    clamav \
    clamav-daemon \
    clamav-clamdscan \
    freshclam \
    libstdc++

COPY bin/entry.sh /
RUN chmod 500 /usr/bin/aws-lambda-rie /entry.sh

# Setup ClamAV config
COPY conf /etc/clamav
RUN mkdir -p /tmp/clamav/quarantine \
    && chown -R clamav:clamav /tmp/clamav \
    && chown -R clamav:clamav /etc/clamav

# Copy function code
WORKDIR ${FUNCTION_DIR}
COPY . ${FUNCTION_DIR}

ENTRYPOINT [ "/entry.sh", "main.handler" ]
