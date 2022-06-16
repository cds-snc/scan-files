# Define function directory
ARG FUNCTION_DIR="/function"

FROM python:3.9-slim-buster

RUN adduser --system --group python

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends ca-certificates curl git gstreamer1.0-libav libnss3-tools libatk-bridge2.0-0 libcups2-dev libxkbcommon-x11-0 libxcomposite-dev libxrandr2 libgbm-dev libgtk-3-0 libxshmfence-dev gnupg2 postgresql-client openssh-client python3-pip vim wget xz-utils zsh entr unzip clamav clamav-daemon \
    && apt-get autoremove -y && apt-get clean -y

# Include global arg in this stage of the build
ARG FUNCTION_DIR

WORKDIR ${FUNCTION_DIR}

RUN mkdir -p /pymodules
ENV PYTHONPATH=/pymodules

COPY ./requirements.txt ${FUNCTION_DIR}

RUN python3.9 -m pip install -r ${FUNCTION_DIR}/requirements.txt --target /pymodules

# Install the runtime interface client
RUN pip install \
    --target /pymodules \
    awslambdaric

# Install AWS cli
ARG AWS_CLI_VERSION="2.4.5"
RUN curl -sL https://awscli.amazonaws.com/awscli-exe-linux-x86_64-${AWS_CLI_VERSION}.zip -o awscliv2.zip \
 && unzip awscliv2.zip \
 && aws/install \
 && rm -rf \
    awscliv2.zip \
    aws \
    /usr/local/aws-cli/v2/*/dist/aws_completer \
    /usr/local/aws-cli/v2/*/dist/awscli/data/ac.index \
    /usr/local/aws-cli/v2/*/dist/awscli/examples

# Copy function code
COPY . ${FUNCTION_DIR}

# Set build variables
ARG git_sha 
ENV GIT_SHA=$git_sha

# Install lambda runtime interactive environment
ARG RIE_VERSION=1.1
RUN wget -O aws-lambda-rie https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/download/${RIE_VERSION}/aws-lambda-rie \
    && mv aws-lambda-rie /usr/bin/aws-lambda-rie
COPY bin/entry.sh /
RUN chmod 755 /usr/bin/aws-lambda-rie /entry.sh

RUN usermod -a -G clamav python
RUN chown -R python:python ${FUNCTION_DIR}

# Setup ClamAV
RUN mkdir /tmp/clamav_defs
RUN chown -R python:python /tmp/clamav_defs /var/log/clamav
RUN sed -i 's/User clamav/User python/g' /etc/clamav/clamd.conf
RUN sed -i 's/CompressLocalDatabase no/CompressLocalDatabase yes/g' /etc/clamav/freshclam.conf
RUN sed -i 's/DatabaseOwner clamav/DatabaseOwner python/g' /etc/clamav/freshclam.conf

USER python

ENTRYPOINT [ "/entry.sh" ]
CMD [ "main.handler" ]