# dockerfiles

![publish_docs](https://github.com/athackst/dockerfiles/workflows/publish_docs/badge.svg)
![push_dockerfiles](https://github.com/athackst/dockerfiles/workflows/push_dockerfiles/badge.svg)

These are multi-stage docker images I use for developing with [VSCode](https://code.visualstudio.com/).

See [how I develop with vscode and docker](https://www.allisonthackston.com/articles/docker_development.html).

Instructions on how to duplicate my IDE:

* [vscode, docker, and ros2](https://www.allisonthackston.com/articles/vscode_docker_ros2.html)
* [vscode, docker, and github pages](https://www.allisonthackston.com/articles/vscode_docker_github_pages.html)

## Quick start

Grab the docker image from [docker hub](https://hub.docker.com/u/althack).  This repo provides the images in:

* [althack/ros](https://hub.docker.com/r/althack/ros)
* [althack/ros2](https://hub.docker.com/r/althack/ros2)
* [althack/gazebo](https://hub.docker.com/r/althack/gazebo)
* [althack/igntion](https://hub.docker.com/r/althack/ignition)
* [althack/gz](https://hub.docker.com/r/althack/gz)

Then, set up a [vscode workspace](https://github.com/athackst/vscode_ros2_workspace).

## Build from source

Alternatively, you can build all the docker images directly from source.

```bash
./build.py all
```

Or just build one

```bash
./build.py foxy
```

To see help information and build options

```bash
./build.py --help
```
