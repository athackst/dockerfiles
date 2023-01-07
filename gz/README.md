# althack/gz

These are the docker images I use for developing with [VSCode](https://code.visualstudio.com/).
See [the docs](https://athackst.github.io/dockerfiles) or read about  [how I develop with vscode and docker](https://www.allisonthackston.com/articles/docker_development.html).

## Usage

```bash
docker pull althack/gz:garden-base
```

## Organization

The main docker image tags are:


garden
  
* [garden-base](https://github.com/athackst/dockerfiles/blob/main/gz/garden.Dockerfile)
* [garden-dev](https://github.com/athackst/dockerfiles/blob/main/gz/garden.Dockerfile)
* [garden-nvidia](https://github.com/athackst/dockerfiles/blob/main/gz/garden.Dockerfile)


Each image is additionally tagged with the date of creation, which lets you peg to a specific version of packages.

The format is {image-name}-{year}-{month}-{day}