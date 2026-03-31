#!/usr/bin/env bash
set -e

# Ensure ROS_DISTRO is set (or pass it via --env / Docker ARG->ENV)
: "${ROS_DISTRO:?ROS_DISTRO must be set}"

source "/opt/ros/$ROS_DISTRO/setup.bash" --
exec "$@"

