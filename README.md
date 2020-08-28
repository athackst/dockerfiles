# dockerfiles

These are base docker images for developing code.

You can use them as a base image for development with VSCode using container based development.

## Quick start

Create the docker images

```bash
./update.sh all
```

To see help information on the update script

```bash
./update.sh -h
```

-----

## FAQ

__Q: Why build code inside a docker?__

> Re-creatable building environment that can be duplicated in Continuous Integration or sent to others to duplicate issues.

__Q: What is needed to set up vscode to work with docker as a development container?__

> You need to create a non-root user with the same user id and group as your user, and you need to mount your .ssh configuration inside the container.
