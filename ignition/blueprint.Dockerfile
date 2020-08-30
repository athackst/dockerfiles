###########################################
# Base image 
###########################################
FROM ubuntu:18.04 AS base

ENV IGN_DISTRO=blueprint

# Avoid warnings by switching to noninteractive
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y \
  gnupg2 \
  lsb-release \
  sudo \
  wget \
  && rm -rf /var/lib/apt/lists/*

COPY install_base.sh /setup/install_base.sh
RUN ./setup/install_base.sh && rm -rf /var/lib/apt/lists/*


###########################################
# Develop image 
###########################################
FROM base AS dev

ENV GAZEBO_VERSION=2

ENV DEBIAN_FRONTEND=noninteractive
# Install dev tools
COPY install_dev.sh /setup/install_dev.sh
RUN ./setup/install_dev.sh && rm -rf /var/lib/apt/lists/*

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