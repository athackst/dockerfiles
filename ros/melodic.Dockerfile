#############################################
# Created from template ros.dockerfile.jinja
#############################################

###########################################
# Base image 
###########################################
FROM ubuntu:18.04 AS base

ENV DEBIAN_FRONTEND=noninteractive

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
RUN apt-get update && apt-get install -y \
    curl \
    dirmngr \
    gnupg2 \
    lsb-release \
    sudo \
  && sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list' \
  && curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | apt-key add - \
  && apt-get update && apt-get install -y \
    ros-melodic-ros-base \
  && rm -rf /var/lib/apt/lists/*

# Setup environment
ENV LD_LIBRARY_PATH=/opt/ros/melodic/lib
ENV ROS_DISTRO=melodic
ENV ROS_ROOT=/opt/ros/melodic/share/ros
ENV ROS_PACKAGE_PATH=/opt/ros/melodic/share
ENV ROS_MASTER_URI=http://localhost:11311
ENV ROS_PYTHON_VERSION=
ENV ROS_VERSION=1
ENV PATH=/opt/ros/melodic/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV ROSLISP_PACKAGE_DIRECTORIES=
ENV PYTHONPATH=/opt/ros/melodic/lib/python2.7/dist-packages
ENV PKG_CONFIG_PATH=/opt/ros/melodic/lib/pkgconfig
ENV ROS_ETC_DIR=/opt/ros/melodic/etc/ros
ENV CMAKE_PREFIX_PATH=/opt/ros/melodic
ENV DEBIAN_FRONTEND=

###########################################
# Develop image 
###########################################
FROM base AS dev

ENV DEBIAN_FRONTEND=noninteractive
# Install dev tools
RUN apt-get update && apt-get install -y \
    python-rosdep \
    python-rosinstall \
    python-rosinstall-generator \
    python-wstool \
    python-pip \
    python-pep8 \
    python-autopep8 \
    pylint \
    build-essential \
    bash-completion \
    git \
    vim \
  && rm -rf /var/lib/apt/lists/* \
  && rosdep init || echo "rosdep already initialized"

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
  && echo "if [ -f /opt/ros/${ROS_DISTRO}/setup.bash ]; then source /opt/ros/${ROS_DISTRO}/setup.bash; fi" >> /home/$USERNAME/.bashrc
ENV DEBIAN_FRONTEND=

###########################################
# Full image 
###########################################
FROM dev AS full

ENV DEBIAN_FRONTEND=noninteractive
# Install the full release
RUN apt-get update && apt-get install -y \
  ros-melodic-desktop \
  && rm -rf /var/lib/apt/lists/*
ENV DEBIAN_FRONTEND=

###########################################
#  Full+Gazebo image 
###########################################
FROM full AS gazebo

ENV DEBIAN_FRONTEND=noninteractive
# Install gazebo
RUN apt-get update && apt-get install -y \
  ros-melodic-gazebo* \
  && rm -rf /var/lib/apt/lists/*
ENV DEBIAN_FRONTEND=

###########################################
#  Full+Gazebo+Nvidia image 
###########################################

FROM gazebo AS gazebo-nvidia

################
# Expose the nvidia driver to allow opengl 
# Dependencies for glvnd and X11.
################
RUN apt-get update \
 && apt-get install -y -qq --no-install-recommends \
  libglvnd0 \
  libgl1 \
  libglx0 \
  libegl1 \
  libxext6 \
  libx11-6

# Env vars for the nvidia-container-runtime.
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES graphics,utility,compute
ENV QT_X11_NO_MITSHM 1