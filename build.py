#!/usr/bin/env python3
"""Update script for dockerfiles."""
import os
import click
import docker
import json
import logging
import re
from datetime import date
from settings import images
from generate import generate as gen

TODAY = date.today()
USER = "athackst"

log = logging.getLogger(__name__)


class StreamLineBuildGenerator(object):
    """Generator for docker streams."""

    def __init__(self, json_data):
        """Initialze with json formatted dictionary.

        Args:
            json_data: The json dictionary
        """
        self.__dict__ = json.loads(json_data)


class Docker(object):
    """Managed docker class to hide complexity with logging output."""

    REGISTRY = "athackst"

    def __init__(self):
        """Initialize docker container from environment."""
        self.client = docker.from_env(timeout=600)
        self.api_client = docker.APIClient()
        self.auth_config = None

    def build(self, context, dockerfile, repository, tag, target, labels):
        """Build the specified container.

        Args:
            context: The path to the context
            dockerfile: The relative path to the dockerfile from the context
            repository: The name of the repository to build
            tag: The tag for the build
            target: The target to build in a multi-stage docker
            labels: Extra label to add to the image
        """
        build_tag = "{registry}/{repository}:{tag}".format(
            registry=Docker.REGISTRY,
            repository=repository,
            tag=tag)
        log.info("Building {context}{dockerfile} {target} as {tag}".format(
            context=context,
            dockerfile=dockerfile,
            target=target,
            tag=build_tag))
        output = self.api_client.build(path=context,
                                       dockerfile=dockerfile,
                                       target=target,
                                       tag=build_tag,
                                       labels=labels,
                                       pull=True)
        self._process_output(output)
        log.info("Done building {}".format(build_tag))

    def tag(self, repository, prev_tag, new_tag):
        """Tag a built image."""
        remote_repository = "{}/{}".format(Docker.REGISTRY, repository)
        image = "{}:{}".format(remote_repository, prev_tag)
        log.info("Taging {image} --> {repository}:{tag}".format(
            image=image,
            repository=remote_repository,
            tag=new_tag))
        self.api_client.tag(
            image=image, repository=remote_repository, tag=new_tag)

    def push(self, repository, tag):
        """Push a built repository:tag to a registry.

        Format: registry/repository:tag

        Args:
            repository: The name of the repository.
            tag: The name of the tag.
        """
        remote_repository = "{}/{}".format(Docker.REGISTRY, repository)
        log.info("Pushing {repository}:{tag}".format(
            repository=remote_repository, tag=tag))
        output = self.api_client.push(repository=remote_repository,
                                      tag=tag,
                                      stream=True,
                                      auth_config=self.auth_config)
        self._process_output(output)

        log.info("Done pushing {repository}:{tag}".format(
            repository=remote_repository, tag=tag))

    def set_auth_config(self):
        """Set the authorization config from environment variables.

        Env:
            username: $DOCKER_USERNAME
            password: $DOCKER_PASSWORD
        """
        self.auth_config = {
            "username": os.getenv('DOCKER_USERNAME'),
            "password": os.getenv('DOCKER_PASSWORD')
        }

    def prune(self):
        """Prune dangling images."""
        self.api_client.prune_images()

    def rmi(self, repository, tag):
        """Remove image by repository and tag."""
        image = "{}/{}:{}".format(Docker.REGISTRY, repository, tag)
        self.api_client.remove_image(image=image)

    def _process_output(self, output):
        if isinstance(output, str):
            output = output.split("\n")

        for line in output:
            if line:
                errors = set()
                try:
                    stream_line = StreamLineBuildGenerator(line)
                    # pylint: disable=no-member

                    if hasattr(stream_line, "status"):
                        log.debug(stream_line.status)

                    elif hasattr(stream_line, "stream"):
                        stream = re.sub("^\n", "", stream_line.stream)
                        stream = re.sub("\n$", "", stream)
                        stream = re.sub(r"\n(\x1B\[0m)$", "\\1", stream)
                        if stream:
                            log.debug(stream)

                    elif hasattr(stream_line, "aux"):
                        if hasattr(stream_line.aux, "Digest"):
                            log.debug("digest: {}".format(
                                stream_line.aux["Digest"]))

                        if hasattr(stream_line.aux, "ID"):
                            log.debug("ID: {}".format(stream_line.aux["ID"]))

                    else:
                        log.debug("not recognized (1): {}".format(line))

                    if hasattr(stream_line, "error"):
                        errors.add(stream_line.error)

                    if hasattr(stream_line, "errorDetail"):
                        errors.add(stream_line.errorDetail["message"])

                        if hasattr(stream_line.errorDetail, "code"):
                            error_code = stream_line.errorDetail["code"]
                            errors.add("Error code: {}".format(error_code))

                except ValueError:
                    log.error("not recognized (2): {}".format(line))

                if errors:
                    message = "problem executing Docker: {}".format(
                        ". ".join(errors))
                    raise SystemError(message)


def build(image, push, clean, auth, verbose):
    """Build the docker images."""
    builds = images()
    if image != 'all':
        builds = {image: images()[image]}

    # Build docker images.
    dockerpy = Docker()
    path_to_script = os.path.dirname(os.path.abspath(__file__))
    if auth:
        dockerpy.set_auth_config()
    for name in builds:
        repository = builds[name]["repository"]
        targets = builds[name]["targets"]
        context = "{path}/{repository}/".format(
            path=path_to_script, repository=repository)
        dockerfile = "{file}.Dockerfile".format(file=name)
        labels = {"version": "{date}".format(date=TODAY)}
        for target in targets:
            latest_tag = "{name}-{target}".format(name=name, target=target)
            dated_tag = "{latest}-{date}".format(latest=latest_tag, date=TODAY)
            dockerpy.build(context=context,
                           dockerfile=dockerfile,
                           repository=repository,
                           tag=latest_tag,
                           target=target,
                           labels=labels)
            dockerpy.tag(repository=repository,
                         prev_tag=latest_tag, new_tag=dated_tag)

            if push:
                dockerpy.push(repository=repository, tag=latest_tag)
                dockerpy.push(repository=repository, tag=dated_tag)
            if clean:
                dockerpy.rmi(repository=repository, tag=dated_tag)
                dockerpy.prune()


@click.command()
@click.option("--generate/--no-generate",
              default=True,
              help="Generate docker files.")
@click.option("--push/--no-push",
              default=False,
              help="Push generated images to DockerHub.")
@click.option("--auth/--no-auth",
              default=False,
              help="Use authorization config from environment.")
@click.option("--clean/--no-clean",
              default=True,
              help="Clean dated content and old images.")
@click.option('--verbose', is_flag=True)
@click.argument("image",
                type=click.Choice(list(images()) + ['all']))
def main(generate, push, clean, auth, verbose, image):
    """Set up logging and trigger build."""
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(message)s')
    ch = logging.StreamHandler()
    if verbose:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    log.addHandler(ch)

    if generate:
        gen(log)

    build(image, push, clean, auth, verbose)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
