#!/bin/bash

set -e

apt-get update
apt-get install -y \
  libignition-plugin-dev \
  libignition-cmake2-dev \
  libignition-gazebo${GAZEBO_VERSION}-dev