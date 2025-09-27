##############################################
# Created from template ros2.dockerfile.jinja
##############################################

###########################################
# Base image
###########################################
FROM nvidia/cuda:13.0.1-cudnn-runtime-ubuntu24.04 AS base

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

RUN apt-get update && apt-get -y upgrade \
    && rm -rf /var/lib/apt/lists/*

# Install common programs
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg2 \
    lsb-release \
    sudo \
    software-properties-common \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install ROS2
RUN sudo add-apt-repository universe \
  && curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null \
  && apt-get update && apt-get install -y --no-install-recommends \
    ros-rolling-ros-base \
    python3-argcomplete \
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
ENV DEBIAN_FRONTEND=

ENV ROS_DISTRO=rolling
ENV AMENT_PREFIX_PATH=/opt/ros/rolling
ENV COLCON_PREFIX_PATH=/opt/ros/rolling
ENV LD_LIBRARY_PATH=/opt/ros/rolling/opt/zenoh_cpp_vendor/lib:/opt/ros/rolling/lib/x86_64-linux-gnu:/opt/ros/rolling/lib
ENV PATH=/opt/ros/rolling/bin:$PATH
ENV PYTHONPATH=/opt/ros/rolling/local/lib/python3.12/dist-packages:/opt/ros/rolling/lib/python3.12/site-packages
ENV ROS_PYTHON_VERSION=3
ENV ROS_VERSION=2
ENV ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET
ENV ROS_LOCALHOST_ONLY=0

CMD ["bash"]

###########################################
#  Develop image
###########################################
FROM base AS dev

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
  bash-completion \
  build-essential \
  cmake \
  gdb \
  git \
  openssh-client \
  python3-argcomplete \
  python3-pip \
  ros-dev-tools \
  ros-rolling-ament-* \
  vim \
  && rm -rf /var/lib/apt/lists/*

RUN rosdep init || echo "rosdep already initialized"

ARG USERNAME=ros
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Check if "ubuntu" user exists, delete it if it does, then create the desired user
RUN if getent passwd ubuntu > /dev/null 2>&1; then \
        userdel -r ubuntu && \
        echo "Deleted existing ubuntu user"; \
    fi && \
    groupadd --gid $USER_GID $USERNAME && \
    useradd -s /bin/bash --uid $USER_UID --gid $USER_GID -m $USERNAME && \
    echo "Created new user $USERNAME"

# Add sudo support for the non-root user
RUN apt-get update && apt-get install -y sudo \
  && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME\
  && chmod 0440 /etc/sudoers.d/$USERNAME \
  && rm -rf /var/lib/apt/lists/*

# Set up autocompletion for user
RUN apt-get update && apt-get install -y --no-install-recommends git-core bash-completion \
  && echo "if [ -f /opt/ros/${ROS_DISTRO}/setup.bash ]; then source /opt/ros/${ROS_DISTRO}/setup.bash; fi" >> /home/$USERNAME/.bashrc \
  && echo "if [ -f /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash ]; then source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash; fi" >> /home/$USERNAME/.bashrc \
  && rm -rf /var/lib/apt/lists/*

ENV DEBIAN_FRONTEND=
ENV AMENT_CPPCHECK_ALLOW_SLOW_VERSIONS=1

###########################################
#  Full image
###########################################
FROM dev AS full

ENV DEBIAN_FRONTEND=noninteractive
# Install the full release
RUN apt-get update && apt-get install -y --no-install-recommends \
  ros-rolling-desktop \
  && rm -rf /var/lib/apt/lists/*
ENV DEBIAN_FRONTEND=

ENV LD_LIBRARY_PATH=/opt/ros/rolling/opt/zenoh_cpp_vendor/lib:/opt/ros/rolling/opt/gz_math_vendor/lib:/opt/ros/rolling/opt/gz_utils_vendor/lib:/opt/ros/rolling/opt/gz_cmake_vendor/lib:/opt/ros/rolling/opt/rviz_ogre_vendor/lib:/opt/ros/rolling/lib/x86_64-linux-gnu:/opt/ros/rolling/lib
ENV CMAKE_PREFIX_PATH=/opt/ros/rolling/opt/gz_math_vendor:/opt/ros/rolling/opt/gz_utils_vendor:/opt/ros/rolling/opt/gz_cmake_vendor

###########################################
#  Full+Gazebo image
###########################################
FROM full AS gazebo

ENV DEBIAN_FRONTEND=noninteractive
# Install gazebo
RUN wget https://packages.osrfoundation.org/gazebo.gpg -O /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg \
  && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null \
  && apt-get update && apt-get install -q -y --no-install-recommends \
    ros-rolling-ros-gz \
  && rm -rf /var/lib/apt/lists/*
ENV DEBIAN_FRONTEND=

ENV LD_LIBRARY_PATH=/opt/ros/rolling/opt/zenoh_cpp_vendor/lib:/opt/ros/rolling/opt/gz_sim_vendor/lib:/opt/ros/rolling/opt/gz_sensors_vendor/lib:/opt/ros/rolling/opt/gz_physics_vendor/lib:/opt/ros/rolling/opt/sdformat_vendor/lib:/opt/ros/rolling/opt/gz_gui_vendor/lib:/opt/ros/rolling/opt/gz_transport_vendor/lib:/opt/ros/rolling/opt/gz_rendering_vendor/lib:/opt/ros/rolling/opt/gz_plugin_vendor/lib:/opt/ros/rolling/opt/gz_fuel_tools_vendor/lib:/opt/ros/rolling/opt/gz_msgs_vendor/lib:/opt/ros/rolling/opt/gz_common_vendor/lib:/opt/ros/rolling/opt/gz_math_vendor/lib:/opt/ros/rolling/opt/gz_utils_vendor/lib:/opt/ros/rolling/opt/gz_tools_vendor/lib:/opt/ros/rolling/opt/gz_ogre_next_vendor/lib:/opt/ros/rolling/opt/gz_dartsim_vendor/lib:/opt/ros/rolling/opt/gz_cmake_vendor/lib:/opt/ros/rolling/opt/rviz_ogre_vendor/lib:/opt/ros/rolling/lib/x86_64-linux-gnu:/opt/ros/rolling/lib
ENV GZ_SIM_RESOURCE_PATH=/opt/ros/rolling/share
ENV GZ_CONFIG_PATH=/opt/ros/rolling/opt/gz_sim_vendor/share/gz:/opt/ros/rolling/opt/sdformat_vendor/share/gz:/opt/ros/rolling/opt/gz_gui_vendor/share/gz:/opt/ros/rolling/opt/gz_transport_vendor/share/gz:/opt/ros/rolling/opt/gz_rendering_vendor/share/gz:/opt/ros/rolling/opt/gz_plugin_vendor/share/gz:/opt/ros/rolling/opt/gz_fuel_tools_vendor/share/gz:/opt/ros/rolling/opt/gz_msgs_vendor/share/gz:/opt/ros/rolling/opt/gz_common_vendor/share/gz
ENV PATH=/opt/ros/rolling/opt/gz_msgs_vendor/bin:/opt/ros/rolling/opt/gz_tools_vendor/bin:/opt/ros/rolling/opt/gz_ogre_next_vendor/bin:/opt/ros/rolling/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV CMAKE_PREFIX_PATH=/opt/ros/rolling/opt/gz_math_vendor:/opt/ros/rolling/opt/gz_utils_vendor:/opt/ros/rolling/opt/gz_ogre_next_vendor:/opt/ros/rolling/opt/gz_dartsim_vendor:/opt/ros/rolling/opt/gz_cmake_vendor:/opt/ros/rolling/opt/gz_sim_vendor:/opt/ros/rolling/opt/gz_sensors_vendor:/opt/ros/rolling/opt/gz_physics_vendor:/opt/ros/rolling/opt/sdformat_vendor:/opt/ros/rolling/opt/gz_gui_vendor:/opt/ros/rolling/opt/gz_transport_vendor:/opt/ros/rolling/opt/gz_rendering_vendor:/opt/ros/rolling/opt/gz_plugin_vendor:/opt/ros/rolling/opt/gz_fuel_tools_vendor:/opt/ros/rolling/opt/gz_msgs_vendor:/opt/ros/rolling/opt/gz_common_vendor:/opt/ros/rolling/opt/gz_tools_vendor