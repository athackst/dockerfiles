# althack/ros2

These are the docker images I use for developing with [VSCode](https://code.visualstudio.com/).
See [the docs](https://athackst.github.io/dockerfiles) or read about  [how I develop with vscode and docker](https://www.allisonthackston.com/articles/docker_development.html).

## Usage

```bash
docker pull althack/ros2:rolling-base
```

## Organization

The main docker image tags are:


rolling
  
* [rolling-base](https://github.com/athackst/dockerfiles/blob/main/ros2/rolling.Dockerfile)
* [rolling-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/rolling.Dockerfile)
* [rolling-full](https://github.com/athackst/dockerfiles/blob/main/ros2/rolling.Dockerfile)
* [rolling-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/rolling.Dockerfile)

iron
  
* [iron-base](https://github.com/athackst/dockerfiles/blob/main/ros2/iron.Dockerfile)
* [iron-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/iron.Dockerfile)
* [iron-full](https://github.com/athackst/dockerfiles/blob/main/ros2/iron.Dockerfile)
* [iron-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/iron.Dockerfile)

iron-cuda
  
* [iron-cuda-base](https://github.com/athackst/dockerfiles/blob/main/ros2/iron-cuda.Dockerfile)
* [iron-cuda-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/iron-cuda.Dockerfile)
* [iron-cuda-full](https://github.com/athackst/dockerfiles/blob/main/ros2/iron-cuda.Dockerfile)
* [iron-cuda-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/iron-cuda.Dockerfile)

humble
  
* [humble-base](https://github.com/athackst/dockerfiles/blob/main/ros2/humble.Dockerfile)
* [humble-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/humble.Dockerfile)
* [humble-full](https://github.com/athackst/dockerfiles/blob/main/ros2/humble.Dockerfile)
* [humble-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/humble.Dockerfile)

humble-cuda
  
* [humble-cuda-base](https://github.com/athackst/dockerfiles/blob/main/ros2/humble-cuda.Dockerfile)
* [humble-cuda-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/humble-cuda.Dockerfile)
* [humble-cuda-full](https://github.com/athackst/dockerfiles/blob/main/ros2/humble-cuda.Dockerfile)
* [humble-cuda-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/humble-cuda.Dockerfile)

galactic (eol)
  
* [galactic-base](https://github.com/athackst/dockerfiles/blob/main/ros2/galactic.Dockerfile)
* [galactic-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/galactic.Dockerfile)
* [galactic-full](https://github.com/athackst/dockerfiles/blob/main/ros2/galactic.Dockerfile)
* [galactic-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/galactic.Dockerfile)

galactic-cuda (eol)
  
* [galactic-cuda-base](https://github.com/athackst/dockerfiles/blob/main/ros2/galactic-cuda.Dockerfile)
* [galactic-cuda-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/galactic-cuda.Dockerfile)
* [galactic-cuda-full](https://github.com/athackst/dockerfiles/blob/main/ros2/galactic-cuda.Dockerfile)
* [galactic-cuda-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/galactic-cuda.Dockerfile)

foxy (eol)
  
* [foxy-base](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy.Dockerfile)
* [foxy-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy.Dockerfile)
* [foxy-full](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy.Dockerfile)
* [foxy-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy.Dockerfile)

foxy-cuda (eol)
  
* [foxy-cuda-base](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy-cuda.Dockerfile)
* [foxy-cuda-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy-cuda.Dockerfile)
* [foxy-cuda-full](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy-cuda.Dockerfile)
* [foxy-cuda-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/foxy-cuda.Dockerfile)

eloquent (eol)
  
* [eloquent-base](https://github.com/athackst/dockerfiles/blob/main/ros2/eloquent.Dockerfile)
* [eloquent-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/eloquent.Dockerfile)
* [eloquent-full](https://github.com/athackst/dockerfiles/blob/main/ros2/eloquent.Dockerfile)
* [eloquent-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/eloquent.Dockerfile)

dashing (eol)
  
* [dashing-base](https://github.com/athackst/dockerfiles/blob/main/ros2/dashing.Dockerfile)
* [dashing-dev](https://github.com/athackst/dockerfiles/blob/main/ros2/dashing.Dockerfile)
* [dashing-full](https://github.com/athackst/dockerfiles/blob/main/ros2/dashing.Dockerfile)
* [dashing-gazebo](https://github.com/athackst/dockerfiles/blob/main/ros2/dashing.Dockerfile)


Each image is additionally tagged with the date of creation, which lets you peg to a specific version of packages.

The format is {image-name}-{year}-{month}-{day}