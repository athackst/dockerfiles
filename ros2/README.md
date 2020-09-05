# athackst/ros2

These are the docker images I use for developing with [VSCode](https://code.visualstudio.com/).
See [the docs](https://athackst.github.io/dockerfiles) or read about  [how I develop with vscode and docker](https://www.allisonthackston.com/articles/docker_development.html).

## Usage

```bash
docker pull athackst/ros2:foxy-base
```

## Organization

The main docker image tags are:

* [foxy-base](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy.Dockerfile)
* [foxy-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy.Dockerfile)
* [foxy-full](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy.Dockerfile)
* [foxy-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy.Dockerfile)
* [eloquent-base](https://github.com/athackst/dockerfiles/blob/main/ros2/eloquent.Dockerfile)
* [eloquent-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/eloquent.Dockerfile)
* [eloquent-full](https://github.com/athackst/dockerfiles/blob/main/ros2/eloquent.Dockerfile)
* [eloquent-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/eloquent.Dockerfile)
* [dashing-base](https://github.com/athackst/dockerfiles/blob/main/ros2/dashing.Dockerfile)
* [dashing-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/dashing.Dockerfile)
* [dashing-full](https://github.com/athackst/dockerfiles/blob/main/ros2/dashing.Dockerfile)
* [dashing-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/dashing.Dockerfile)

Each image is additionally tagged with the date of creation, which lets you peg to a specific version of packages.

The format is {image-name}-{year}-{month}-{day}