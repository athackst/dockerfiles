##################################################
# Created from template gz.dockerfile.jinja
##################################################

###########################################
# Base image
###########################################
FROM nvidia/cuda:12.8.1-runtime-ubuntu24.04 AS base

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Install language
RUN apt-get update && apt-get install -y --no-install-recommends \
  locales \
  && locale-gen en_US.UTF-8 \
  && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
  && rm -rf /var/lib/apt/lists/*
ENV LANG=en_US.UTF-8

# Install timezone
RUN ln -fs /usr/share/zoneinfo/UTC /etc/localtime \
  && export DEBIAN_FRONTEND=noninteractive \
  && apt-get update \
  && apt-get install -y --no-install-recommends tzdata \
  && dpkg-reconfigure --frontend noninteractive tzdata \
  && rm -rf /var/lib/apt/lists/*


# install packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    python3-argcomplete \
    sudo \
    wget \
  && rm -rf /var/lib/apt/lists/*

# Setup gazebo apt sources
RUN curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] https://packages.osrfoundation.org/gazebo/ubuntu-prerelease $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/gazebo-prerelease.list > /dev/null

# Install gazebo
RUN apt-get update && apt-get install -y --no-install-recommends \
    gz-jetty \
  && rm -rf /var/lib/apt/lists/*

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
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=graphics,utility,compute
ENV QT_X11_NO_MITSHM=1

ARG USERNAME=ros
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Find and replace any user with matching UID
RUN set -eux; \
    existing_user=$(getent passwd "$USER_UID" | cut -d: -f1 || true); \
    if [ -n "$existing_user" ]; then \
        usermod -l $USERNAME -d /home/$USERNAME -m $existing_user && \
        groupmod -n $USERNAME $existing_user && \
        echo "Renamed $existing_user to $USERNAME"; \
    else \
        groupadd --gid $USER_GID $USERNAME && \
        useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME && \
        echo "Created new user $USERNAME"; \
    fi

# Ensure necessary directories and permissions
RUN mkdir -p /home/$USERNAME /run/user/$USER_UID && \
    chown -R $USER_UID:$USER_GID /home/$USERNAME /run/user/$USER_UID

# Add sudo support for the non-root user
RUN apt-get update && apt-get install -y --no-install-recommends sudo \
  && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME \
  && chmod 0440 /etc/sudoers.d/$USERNAME \
  && rm -rf /var/lib/apt/lists/*

# Set up autocompletion for user
RUN apt-get update && apt-get install -y --no-install-recommends git-core bash-completion \
  && echo "if [ -f /opt/ros/${ROS_DISTRO}/setup.bash ]; then source /opt/ros/${ROS_DISTRO}/setup.bash; fi" >> /home/$USERNAME/.bashrc \
  && rm -rf /var/lib/apt/lists/* \
  && touch /home/$USERNAME/.sudo_as_admin_successful

###########################################
# Develop image
###########################################
FROM base AS dev

ENV DEBIAN_FRONTEND=noninteractive
# Install dev tools

# Setup ROS Apt sources
RUN curl -L -s -o /tmp/ros2-apt-source.deb https://github.com/ros-infrastructure/ros-apt-source/releases/download/1.1.0/ros2-apt-source_1.1.0.$(lsb_release -cs)_all.deb \
    && apt-get update \
    && apt-get install /tmp/ros2-apt-source.deb \
    && rm -f /tmp/ros2-apt-source.deb \
    && rm -rf /var/lib/apt/lists/*

# Get dev tools
RUN apt-get update && apt-get install -y --no-install-recommends\
    build-essential \
    clang \
    cmake \
    git \
    git \
    lcov \
    libasio-dev \
    libc++-dev \
    libc++abi-dev \
    libssl-dev \
    libtinyxml2-dev \
    python3-colcon-common-extensions \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-vcstool \
    python3-wheel \
    vim \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces/gazebo/src
# Get sources
RUN wget https://raw.githubusercontent.com/gazebo-tooling/gazebodistro/refs/heads/master/collection-jetty.yaml \
  && vcs import < collection-jetty.yaml \
  # Get dependencies
  && apt-get update && apt-get install -q -y --no-install-recommends \
      $(sort -u $(find . -iname 'packages-'`lsb_release -cs`'.apt' -o -iname 'packages.apt' | grep -v '/\.git/') | sed '/gz\|sdf/d' | tr '\n' ' ')

ENV DEBIAN_FRONTEND=