# athackst/ignition

These are the docker images I use for developing with [VSCode](https://code.visualstudio.com/).
See [the docs](https://athackst.github.io/dockerfiles) or read about  [how I develop with vscode and docker](https://www.allisonthackston.com/articles/docker_development.html).

## Usage

```bash
docker pull athackst/ignition:citadel-base
```

## Organization

The main docker image tags are:

* [citadel-base](https://github.com/athackst/dockerfiles/blob/main/ignition/citadel.Dockerfile)
* [citadel-dev](https://github.com/athackst/dockerfiles/blob/main/ignition/citadel.Dockerfile)
* [blueprint-base](https://github.com/athackst/dockerfiles/blob/main/ignition/blueprint.Dockerfile)
* [blueprint-dev](https://github.com/athackst/dockerfiles/blob/main/ignition/blueprint.Dockerfile)

Each image is additionally tagged with the date of creation, which lets you peg to a specific version of packages.

The format is {image-name}-{year}-{month}-{day}