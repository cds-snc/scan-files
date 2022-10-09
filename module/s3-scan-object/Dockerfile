ARG BASE_IMAGE=node:14.20.1-alpine3.16@sha256:50808db1777e35ca156d06cfd31fa377febe82df6f26b8413a47c12dcbf5e6c5

# Builder to install lambda dependencies
FROM ${BASE_IMAGE} as builder

ARG APP_DIR="/app"

WORKDIR ${APP_DIR}

RUN apk add --no-cache \
    autoconf \
    automake \
    build-base \
    libcurl \
    libexecinfo-dev \
    libstdc++ \
    libtool \
    make \
    cmake \
    python3

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

# Create non-root user to run the lambda
RUN addgroup --gid 10001 --system ${USER} && \
    adduser --uid 10000 --system --ingroup ${USER} --home /home/${USER} ${USER} && \
    chown --recursive ${USER}:${USER} ${APP_DIR}

USER ${USER}

ENTRYPOINT ["/usr/local/bin/npx", "aws-lambda-ric", "app.handler"]
