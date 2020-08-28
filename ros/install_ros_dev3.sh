#!/bin/bash
set -e

apt-get update
apt-get install -y \
    python3-rosdep \
    python3-rosinstall \
    python3-rosinstall-generator \
    python3-wstool \
    python3-pip \
    pylint3 \
    build-essential \
    bash-completion \
    git \
    vim

rosdep init || echo "rosdep already initialized"
