# althack/ros

These are the docker images I use for developing with [VSCode](https://code.visualstudio.com/).
See [the docs](https://athackst.github.io/dockerfiles) or read about  [how I develop with vscode and docker](https://www.allisonthackston.com/articles/docker_development.html).

## Usage

```bash
docker pull althack/ros:noetic-base
```

## Organization

The main docker image tags are:

* [noetic-base](https://github.com/athackst/dockerfiles/blob/main/ros/noetic.Dockerfile)
* [noetic-dev](https://github.com/athackst/dockerfiles/blob/main/ros/noetic.Dockerfile)
* [noetic-full](https://github.com/athackst/dockerfiles/blob/main/ros/noetic.Dockerfile)
* [noetic-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros/noetic.Dockerfile)
* [melodic-base](https://github.com/athackst/dockerfiles/blob/main/ros/melodic.Dockerfile)
* [melodic-dev](https://github.com/athackst/dockerfiles/blob/main/ros/melodic.Dockerfile)
* [melodic-full](https://github.com/athackst/dockerfiles/blob/main/ros/melodic.Dockerfile)
* [melodic-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros/melodic.Dockerfile)
* [kinetic-base](https://github.com/athackst/dockerfiles/blob/main/ros/kinetic.Dockerfile)
* [kinetic-dev](https://github.com/athackst/dockerfiles/blob/main/ros/kinetic.Dockerfile)
* [kinetic-full](https://github.com/athackst/dockerfiles/blob/main/ros/kinetic.Dockerfile)
* [kinetic-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros/kinetic.Dockerfile)

Each image is additionally tagged with the date of creation, which lets you peg to a specific version of packages.

The format is {image-name}-{year}-{month}-{day}