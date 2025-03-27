# Docker Compose

This repository includes some docker compose configurations for running the Gazebo simulation environments inside a container with GUI support

## Installation

To use these Docker Compose files, you'll need to have Docker and Docker Compose installed on your system.

- Install Docker: Follow the official installation guide for your platform:
<https://docs.docker.com/get-docker/>

- Install Docker Compose (if not included with Docker):
<https://docs.docker.com/compose/install/>

To verify your installation, run:

```bash
docker --version
docker-compose --version
```

## Usage

Before starting the containers, make sure to allow Docker to access the X server on your host machine by running 

```bash
xhost +local:docker
```

The run the docker-compose script for your version

```bash
docker-compose -f {{version}}-docker-compose.yml up
```

=== "harmonic"

    ```bash
    docker-compose -f harmonic-docker-compose.yml up
    ```

=== "ionic"

    ```bash
    docker-compose -f ionic-docker-compose.yml up
    ```

## Notes

- Both Docker Compose files use host networking (network_mode: host) to simplify GUI display setup.

- GUI support is enabled by sharing the X11 socket and setting appropriate environment variables (`DISPLAY`, `XAUTHORITY`).

- Software rendering is enforced (`LIBGL_ALWAYS_SOFTWARE=1`) for compatibility.

- The containers will launch `gz sim` as the default command.
