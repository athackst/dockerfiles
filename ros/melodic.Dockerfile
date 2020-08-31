#############################################
# Created from template ros.dockerfile.jinja
#############################################

###########################################
# Base image 
###########################################
FROM ubuntu:18.04 AS base

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=melodic

# Install language
RUN apt-get update && apt-get install -y \
  locales \
  && locale-gen en_US.UTF-8 \
  && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
  && rm -rf /var/lib/apt/lists/*
ENV LANG en_US.UTF-8

# Install timezone
RUN ln -fs /usr/share/zoneinfo/UTC /etc/localtime \
  && export DEBIAN_FRONTEND=noninteractive \
  && apt-get update \
  && apt-get install -y tzdata \
  && dpkg-reconfigure --frontend noninteractive tzdata \
  && rm -rf /var/lib/apt/lists/*

# Install ROS
COPY install_ros_base.sh /setup/install_ros_base.sh
RUN /setup/install_ros_base.sh && rm -rf /var/lib/apt/lists/*

# Setup environment
ENV LD_LIBRARY_PATH=/opt/ros/$ROS_DISTRO/lib:$LD_LIBRARY_PATH
ENV ROS_ROOT=/opt/ros/$ROS_DISTRO/share/ros
ENV ROS_PACKAGE_PATH=/opt/ros/$ROS_DISTRO/share
ENV ROS_MASTER_URI=http://localhost:11311
ENV ROS_PYTHON_VERSION=2
ENV ROS_VERSION=1
ENV PATH=/opt/ros/$ROS_DISTRO/bin:$PATH
ENV ROSLISP_PACKAGE_DIRECTORIES=
ENV PYTHONPATH=/opt/ros/${ROS_DISTRO}/lib/python2.7/dist-packages:$PYTHONPATH
ENV PKG_CONFIG_PATH=/opt/ros/$ROS_DISTRO/lib/pkgconfig:$PKG_CONFIG_PATH
ENV ROS_ETC_DIR=/opt/ros/$ROS_DISTRO/etc/ros
ENV CMAKE_PREFIX_PATH=/opt/ros/$ROS_DISTRO:$CMAKE_PREFIX_PATH
ENV DEBIAN_FRONTEND=

###########################################
# Develop image 
###########################################
FROM base AS dev

ENV DEBIAN_FRONTEND=noninteractive
# Install dev tools
COPY install_ros_dev2.sh /setup/install_ros_dev.sh
RUN /setup/install_ros_dev.sh && rm -rf /var/lib/apt/lists/*

ARG USERNAME=ros
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create a non-root user
RUN groupadd --gid $USER_GID $USERNAME \
  && useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME \
  # [Optional] Add sudo support for the non-root user
  && apt-get update \
  && apt-get install -y sudo \
  && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME\
  && chmod 0440 /etc/sudoers.d/$USERNAME \
  # Cleanup
  && rm -rf /var/lib/apt/lists/* \
  && echo "source /usr/share/bash-completion/completions/git" >> /home/$USERNAME/.bashrc \
  && echo "source /opt/ros/${ROS_DISTRO}/setup.bash" >> /home/$USERNAME/.bashrc

ENV DEBIAN_FRONTEND=

###########################################
# Full image 
###########################################
FROM dev AS full

ENV DEBIAN_FRONTEND=noninteractive
# Install the full release
RUN apt-get update && apt-get install -y \
  ros-${ROS_DISTRO}-desktop \
  && rm -rf /var/lib/apt/lists/*
ENV DEBIAN_FRONTEND=

###########################################
#  Full+Gazebo image 
###########################################
FROM full AS gazebo

ENV DEBIAN_FRONTEND=noninteractive
# Install gazebo
RUN apt-get update && apt-get install -y \
  ros-${ROS_DISTRO}-gazebo* \
  && rm -rf /var/lib/apt/lists/*
ENV DEBIAN_FRONTEND=