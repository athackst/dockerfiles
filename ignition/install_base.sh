#!/bin/bash

set -e

# install packages
apt-get update
apt-get install -q -y \
    dirmngr \
    gnupg2 \
    lsb-release \
    wget

sh -c 'echo "deb http://packages.osrfoundation.org/gazebo/ubuntu-stable `lsb_release -cs` main" > /etc/apt/sources.list.d/gazebo-stable.list'
wget http://packages.osrfoundation.org/gazebo.key -O - | apt-key add -
apt-get update
apt-get install -y ignition-${IGN_DISTRO}
