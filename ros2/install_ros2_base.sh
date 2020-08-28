#/bin/sh
set -e

# get dependencies
apt-get update
apt-get install -y \
  curl \
  gnupg2 \
  lsb-release \

curl http://repo.ros2.org/repos.key | apt-key add -

# add repository to sources list
sh -c 'echo "deb [arch=amd64,arm64] http://packages.ros.org/ros2/ubuntu `lsb_release -cs` main" > /etc/apt/sources.list.d/ros2-latest.list'

# install ROS2
apt-get update
apt-get install -y \
  ros-$ROS_DISTRO-ros-base \
  python3-argcomplete
