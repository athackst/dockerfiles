# althack/ros2

These are the docker images I use for developing with [VSCode](https://code.visualstudio.com/).
See [the docs](https://athackst.github.io/dockerfiles) or read about  [how I develop with vscode and docker](https://www.allisonthackston.com/articles/docker_development.html).

## Usage

```bash
docker pull althack/ros2:humble-base
```

## Organization

The main docker image tags are:

* [humble-base](https://github.com/athackst/dockerfiles/blob/main/ros2/humble.Dockerfile)
* [humble-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/humble.Dockerfile)
* [humble-full](https://github.com/athackst/dockerfiles/blob/main/ros2/humble.Dockerfile)
* [humble-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/humble.Dockerfile)
* [humble-cuda-base](https://github.com/athackst/dockerfiles/blob/main/ros2/humble-cuda.Dockerfile)
* [humble-cuda-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/humble-cuda.Dockerfile)
* [humble-cuda-full](https://github.com/athackst/dockerfiles/blob/main/ros2/humble-cuda.Dockerfile)
* [humble-cuda-gazebo-nvidia](https://github.com/athackst/dockerfiles/blob/main/ros2/humble-cuda.Dockerfile)
* [galactic-base](https://github.com/athackst/dockerfiles/blob/main/ros2/galactic.Dockerfile)
* [galactic-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/galactic.Dockerfile)
* [galactic-full](https://github.com/athackst/dockerfiles/blob/main/ros2/galactic.Dockerfile)
* [galactic-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/galactic.Dockerfile)
* [galactic-cuda-base](https://github.com/athackst/dockerfiles/blob/main/ros2/galactic-cuda.Dockerfile)
* [galactic-cuda-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/galactic-cuda.Dockerfile)
* [galactic-cuda-full](https://github.com/athackst/dockerfiles/blob/main/ros2/galactic-cuda.Dockerfile)
* [galactic-cuda-gazebo-nvidia](https://github.com/athackst/dockerfiles/blob/main/ros2/galactic-cuda.Dockerfile)
* [foxy-base](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy.Dockerfile)
* [foxy-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy.Dockerfile)
* [foxy-full](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy.Dockerfile)
* [foxy-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy.Dockerfile)
* [foxy-cuda-base](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy-cuda.Dockerfile)
* [foxy-cuda-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy-cuda.Dockerfile)
* [foxy-cuda-full](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy-cuda.Dockerfile)
* [foxy-cuda-gazebo-nvidia](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy-cuda.Dockerfile)
* [eloquent-base](https://github.com/athackst/dockerfiles/blob/main/ros2/eloquent.Dockerfile) (eol)
* [eloquent-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/eloquent.Dockerfile) (eol)
* [eloquent-full](https://github.com/athackst/dockerfiles/blob/main/ros2/eloquent.Dockerfile) (eol)
* [eloquent-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/eloquent.Dockerfile) (eol)
* [dashing-base](https://github.com/athackst/dockerfiles/blob/main/ros2/dashing.Dockerfile) (eol)
* [dashing-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/dashing.Dockerfile) (eol)
* [dashing-full](https://github.com/athackst/dockerfiles/blob/main/ros2/dashing.Dockerfile) (eol)
* [dashing-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/dashing.Dockerfile) (eol)

Each image is additionally tagged with the date of creation, which lets you peg to a specific version of packages.

The format is {image-name}-{year}-{month}-{day}