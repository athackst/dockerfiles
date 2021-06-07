#!/usr/bin/env python3
"""Update script for dockerfiles."""
import os
import click
import docker
import logging
from datetime import date
from settings import images
from generate import generate as gen

TODAY = date.today()
USER = "althack"

log = logging.getLogger(__name__)


def auth_config():
    """Set the authorization config from environment variables.

    Env:
        username: $DOCKER_USERNAME
        password: $DOCKER_PASSWORD
    """
    if os.getenv('DOCKER_USERNAME') and os.getenv('DOCKER_PASSWORD'):
        return {
            "username": os.getenv('DOCKER_USERNAME'),
            "password": os.getenv('DOCKER_PASSWORD')
        }
    return None


def docker_push():
    """Set whether or not to push from environment variables.

    Env:
        push: $DOCKER_PUSH
    """
    return os.getenv('DOCKER_PUSH')


def docker_clean():
    """Set whether or not to clean images from environment variables.

    Env:
        push: $DOCKER_CLEAN
    """
    return os.getenv('DOCKER_CLEAN')


class Docker(object):
    """Managed docker class to hide complexity with logging output."""

    def __init__(self, auth_config=None):
        """Initialize docker container from environment."""
        # 600 timeout increases likelihood that push will be successful.
        # May need adjustmet.
        self.client = docker.from_env(timeout=600)
        self.api_client = docker.APIClient()
        self.auth_config = auth_config

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
        build_tag = "{repository}:{tag}".format(
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
                                       pull=True,
                                       decode=True)
        self._process_output(output)
        log.info("Done building {}".format(build_tag))

    def tag(self, repository, prev_tag, new_tag):
        """Tag a built image."""
        image = "{}:{}".format(repository, prev_tag)
        log.info("Taging {image} --> {repository}:{tag}".format(
            image=image,
            repository=repository,
            tag=new_tag))
        self.api_client.tag(
            image=image, repository=repository, tag=new_tag)

    def push(self, repository, tag):
        """Push a built repository:tag to a registry.

        Format: repository:tag

        Args:
            repository: The name of the repository.
            tag: The name of the tag.
        """
        log.info("Pushing {repository}:{tag}".format(
            repository=repository, tag=tag))
        output = self.api_client.push(repository=repository,
                                      tag=tag,
                                      stream=True,
                                      decode=True,
                                      auth_config=self.auth_config)
        self._process_output(output)

        log.info("Done pushing {repository}:{tag}".format(
            repository=repository, tag=tag))

    def prune(self):
        """Prune dangling images."""
        self.api_client.prune_images()

    def rmi(self, repository, tag):
        """Remove image by repository and tag."""
        image = "{}:{}".format(repository, tag)
        self.api_client.remove_image(image=image)

    def _process_output(self, output):
        for line in output:
            errors = set()
            try:
                if "status" in line:
                    log.debug(line["status"].rstrip())

                elif "stream" in line:
                    if line["stream"].rstrip():
                        log.debug(line["stream"].rstrip())

                elif "aux" in line:
                    if "Digest" in line["aux"]:
                        log.debug("digest: {}".format(
                            line["aux"]["Digest"].rstrip()))

                    if "ID" in line["aux"]:
                        log.debug("ID: {}".format(line["aux"]["ID"].rstrip()))

                else:
                    log.debug("not recognized (1): {}".format(line))

                if "error" in line:
                    errors.add(line["error"].rstrip())

                if "errorDetail" in line:
                    if "message" in line["errorDetail"]:
                        errors.add(line["errorDetail"]["message"].rstrip())

                    if "code" in line["errorDetail"]:
                        error_code = line["errorDetail"]["code"]
                        errors.add("Error code: {}".format(error_code))

            except ValueError:
                log.error("not recognized (2): {}".format(line))

            if errors:
                message = "problem executing Docker: {}".format(
                    ". ".join(errors))
                raise SystemError(message)


def build(image, push, clean):
    """Build the docker images."""
    builds = images()
    if image != 'all':
        builds = {image: images()[image]}

    # Build docker images.
    dockerpy = Docker(auth_config())
    path_to_script = os.path.dirname(os.path.abspath(__file__))
    for name in builds:
        repository = "{}/{}".format(USER, builds[name]["repository"])
        targets = builds[name]["targets"]
        context = "{path}/{folder}/".format(
            path=path_to_script, folder=builds[name]["repository"])
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

            if push or docker_push():
                dockerpy.push(repository=repository, tag=latest_tag)
                dockerpy.push(repository=repository, tag=dated_tag)
            if clean or docker_clean():
                dockerpy.rmi(repository=repository, tag=dated_tag)
                dockerpy.prune()


@click.command()
@click.option("--generate/--no-generate",
              default=True,
              help="Generate docker files.")
@click.option("--push/--no-push",
              default=False,
              help="Push generated images to DockerHub.")
@click.option("--clean/--no-clean",
              default=True,
              help="Clean dated content and old images.")
@click.argument("image",
                type=click.Choice(list(images()) + ['all']))
def main(generate, push, clean, image):
    """Set up logging and trigger build."""
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    log.addHandler(ch)

    if generate:
        gen(log)

    build(image, push, clean)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
