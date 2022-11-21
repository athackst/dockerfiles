# Note: You can use any Debian/Ubuntu based image you want. 
FROM mcr.microsoft.com/vscode/devcontainers/base:0-bullseye

# Install jinja
COPY requirements.txt /setup/requirements.txt
RUN apt-get update \ 
    && apt-get install -y python3-pip bash-completion \
    && pip3 install -r /setup/requirements.txt \
    && apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*
