# dockerfiles

[![Documentation](https://github.com/athackst/dockerfiles/actions/workflows/site.yml/badge.svg)](https://github.com/athackst/dockerfiles/actions/workflows/site.yml)
[![Dockerfiles](https://github.com/athackst/dockerfiles/actions/workflows/docker.yml/badge.svg)](https://github.com/athackst/dockerfiles/actions/workflows/docker.yml)

These are multi-stage docker images I use for developing with [VSCode](https://code.visualstudio.com/).

See [how I develop with vscode and docker](https://www.allisonthackston.com/articles/docker_development.html).

Instructions on how to duplicate my IDE:

* [vscode, docker, and ros2](https://www.allisonthackston.com/articles/vscode_docker_ros2.html)

Images will continue to be supported so long as they haven't reached EOL

* **Ignition/Gazebo** https://gazebosim.org/docs/all/releases
* **Gazebo (classic)** https://classic.gazebosim.org/#status
* **ROS** https://wiki.ros.org/Distributions
* **ROS2** https://docs.ros.org/en/rolling/Releases.html

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
./build.py ros2-jazzy-base
```

Or build one distro group

```bash
./build.py ros2-jazzy
```

To see help information and build options

```bash
./build.py --help
```

### Shell completion

Enable tab completion for the current shell session:

```bash
eval "$(_BUILD_PY_COMPLETE=bash_source ./build.py)"
```

Then try:

```bash
./build.py <TAB><TAB>
```

To make completion persistent for bash, add this to your `~/.bashrc`:

```bash
eval "$(_BUILD_PY_COMPLETE=bash_source /path/to/dockerfiles/build.py)"
```

## Template accessor package

You can install the template accessor package in another repo without publishing to PyPI.

Install from GitHub:

```bash
pip install "git+https://github.com/athackst/dockerfiles.git"
```

Pin to a branch/tag/commit:

```bash
pip install "git+https://github.com/athackst/dockerfiles.git@main"
```

For local development (editable install):

```bash
pip install -e .
```

Example usage:

```python
from dockerfiles_templates import Templates

templates = Templates(templates_path="templates.yml")
for entry in templates.entries(eol=False):
    print(entry["family"], entry["name"])
```
