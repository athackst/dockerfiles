#!/bin/bash

set -e

sudo apt-get update
sudo apt-get install -y \
  libignition-plugin-dev \
  libignition-cmake2-dev \
  libignition-gazebo${GAZEBO_VERSION}-dev