# athackst/gazebo

These are the docker images I use for developing with [VSCode](https://code.visualstudio.com/).
See [the docs](https://athackst.github.io/dockerfiles) or read about  [how I develop with vscode and docker](https://www.allisonthackston.com/articles/docker_development.html).

## Usage

```bash
docker pull athackst/gazebo:gazebo11-base
```

## Organization

The main docker image tags are:

* [gazebo11-base](https://github.com/athackst/dockerfiles/blob/main/gazebo/gazebo11.Dockerfile)
* [gazebo11-dev](https://github.com/athackst/dockerfiles/blob/main/gazebo/gazebo11.Dockerfile)
* [gazebo10-base](https://github.com/athackst/dockerfiles/blob/main/gazebo/gazebo10.Dockerfile)
* [gazebo10-dev](https://github.com/athackst/dockerfiles/blob/main/gazebo/gazebo10.Dockerfile)

Each image is additionally tagged with the date of creation, which lets you peg to a specific version of packages.

The format is {image-name}-{year}-{month}-{day}