#!/bin/bash
set -e

apt-get update
apt-get install -y \
    python-rosdep \
    python-rosinstall \
    python-rosinstall-generator \
    python-wstool \
    python-pip \
    pylint \
    build-essential \
    bash-completion \
    git \
    vim

rosdep init || echo "rosdep already initialized"
