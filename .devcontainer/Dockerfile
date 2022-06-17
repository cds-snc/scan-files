# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.183.0/containers/python-3/.devcontainer/base.Dockerfile

# [Choice] Python version: 3, 3.9, 3.8, 3.7, 3.6
ARG VARIANT="3.9"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}

# [Option] Install Node.js
ARG INSTALL_NODE="true"
ARG NODE_VERSION="lts/*"
RUN if [ "${INSTALL_NODE}" = "true" ]; then su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; fi

# Set these in devcontainer.json
ARG SHELLCHECK_VERSION
ARG SHELLCHECK_CHECKSUM

# Install packages
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends clamav clamav-daemon \
    && apt-get autoremove -y && apt-get clean -y

# Install ShellCheck
RUN curl -Lo shellcheck.tar.xz "https://github.com/koalaman/shellcheck/releases/download/v${SHELLCHECK_VERSION}/shellcheck-v${SHELLCHECK_VERSION}.linux.x86_64.tar.xz" \
    && echo "${SHELLCHECK_CHECKSUM} shellcheck.tar.xz" | sha256sum --check \
    && tar -xf shellcheck.tar.xz \
    && mv "shellcheck-v${SHELLCHECK_VERSION}/shellcheck" /usr/local/bin/ \
    && rm -r shellcheck*

# Install Checkov
RUN pip3 install --upgrade requests setuptools \
    && pip3 install --upgrade botocore checkov

COPY .devcontainer/apt-packages.txt ./
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && xargs apt-get -y install --no-install-recommends <apt-packages.txt

# Setup aliases and autocomplete
RUN echo "\n\
complete -C /usr/bin/aws_completer aws\n\
complete -C /usr/local/bin/terraform terraform\n\
complete -C /usr/local/bin/terraform terragrunt\n\
alias tf='terraform'\n\
alias tg='terragrunt'\n\
alias ll='la -la' \n\
alias laws='aws --endpoint-url=http://localstack:4566 --region=ca-central-1'" >> /home/vscode/.zshrc

# Setup AWS Credentials
RUN mkdir -p /home/vscode/.aws 

RUN echo "\n\
[default]\n\
aws_access_key_id=foo\n\
aws_secret_access_key=bar\n\
" >> /home/vscode/.aws/credentials

RUN echo "\n\
[default]\n\
region=ca-central-1\n\
output=json\n\
" >> /home/vscode/.aws/config

# [Optional] If your pip requirements rarely change, uncomment this section to add them to the image.
# COPY requirements.txt /tmp/pip-tmp/
# RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
#    && rm -rf /tmp/pip-tmp

# Setup ClamAV
RUN mkdir -p /tmp/clamav \
 && mkdir -p /tmp/clamav/quarantine \
 && chown -R vscode:vscode /tmp/clamav /var/log/clamav \
 && sed -i 's/User clamav/User vscode/g' /etc/clamav/clamd.conf \
 && sed -i 's/CompressLocalDatabase no/CompressLocalDatabase yes/g' /etc/clamav/freshclam.conf \
 && sed -i 's/DatabaseOwner clamav/DatabaseOwner vscode/g' /etc/clamav/freshclam.conf \
 && sed -i 's=UpdateLogFile /var/log/clamav/freshclam.log=UpdateLogFile /tmp/clamav/freshclam.log=g' /etc/clamav/freshclam.conf


RUN su vscode -c "source /usr/local/share/nvm/nvm.sh && npm install -g typescript" 2>&1
