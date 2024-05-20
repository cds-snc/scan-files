ARG BASE_IMAGE=node:20.13.1-alpine3.19@sha256:291e84d956f1aff38454bbd3da38941461ad569a185c20aa289f71f37ea08e23

# Builder to install lambda dependencies
FROM ${BASE_IMAGE} as builder

ARG APP_DIR="/app"

WORKDIR ${APP_DIR}

RUN apk add --no-cache \
    autoconf \
    automake \
    build-base \
    libcurl \
    libstdc++ \
    libtool \
    make \
    cmake \
    python3

# Install libexecinfo-dev from the Alpine v3.16 repository
RUN apk add --no-cache --update --repository=https://dl-cdn.alpinelinux.org/alpine/v3.16/main/ \
    libexecinfo-dev

RUN npm install --prefix ${APP_DIR}/tmp aws-lambda-ric

COPY app.js package.json yarn.lock .yarnclean ${APP_DIR}/
RUN yarn install \
    --production \
    --frozen-lockfile \
    --non-interactive

RUN cp -a ${APP_DIR}/tmp/node_modules/. ${APP_DIR}/node_modules/ && \
    rm -rf ${APP_DIR}/tmp

RUN yarn autoclean --force

# Lambda function code and dependencies
FROM ${BASE_IMAGE} as lambda

ARG USER="nonroot"
ARG APP_DIR="/app"
ARG git_sha 
ENV GIT_SHA=$git_sha

WORKDIR ${APP_DIR}

COPY --from=builder ${APP_DIR} ${APP_DIR}

# Update Node's cache directory to /tmp so Lambda can write to it
RUN mkdir -p /tmp/.npm && \
    npm config set cache /tmp/.npm --global 

# Create non-root user to run the lambda
RUN addgroup --gid 10001 --system ${USER} && \
    adduser --uid 10000 --system --ingroup ${USER} --home /home/${USER} ${USER} && \
    chown --recursive ${USER}:${USER} ${APP_DIR} && \
    chown --recursive ${USER}:${USER} /tmp/.npm

USER ${USER}

ENTRYPOINT ["/usr/local/bin/npx", "aws-lambda-ric", "app.handler"]