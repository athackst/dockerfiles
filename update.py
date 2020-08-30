#!/usr/bin/env python3
"""Update script for dockerfiles."""
import os
import click
import docker
import generate as gen
from datetime import date

TODAY = date.today()

TARGETS = ["base", "dev", "full", "gazebo"]

USER = "athackst"

IMAGES = {
    "kinetic": {
        "repository": "ros",
        "targets": TARGETS
    },
    "melodic": {
        "repository": "ros",
        "targets": TARGETS
    },
    "noetic": {
        "repository": "ros",
        "targets": TARGETS
    },
    "dashing": {
        "repository": "ros2",
        "targets": TARGETS
    },
    "eloquent": {
        "repository": "ros2",
        "targets": TARGETS
    },
    "foxy": {
        "repository": "ros2",
        "targets": TARGETS
    },
    "pages": {
        "repository": "github",
        "targets": ["dev"]
    },
}


def build_push(context, dockerfile, repository, tag, target, labels, push):
    """Build and optionally push the docker file.

    Args:
      context: The context for the build
      dockerfile: The name of the dockerfile to build
      repository: The name of the repository
      tag: The name of the tag for the image
      target: The name of the target to build
      labels: A dictionary of labels to apply to the image
      push: Indicator to push to DockerHub.
    """
    client = docker.from_env()
    build_tag = "{repository}:{tag}".format(
        repository=repository, tag=tag)
    print("Building {context}{dockerfile} {target} as {tag}".format(
        context=context,
        dockerfile=dockerfile,
        target=target,
        tag=build_tag))
    client.images.build(path=context, dockerfile=dockerfile, target=target,
                        tag=build_tag, labels=labels, pull=True)
    if push:
        client.images.push(repository=repository, tag=tag)
    client.images.prune()


def update(repository, name, targets, push):
    """Build and push docker file.

    Args:
      repository: The name of the folder for context.
            Also the base name of the docker repository on DockerHub.
      build: The name of the base tag
      targets: The name of the target to build from the file
      push: Whether or not to push the resulting image to dockerhub
    """
    path_to_script = os.path.dirname(os.path.abspath(__file__))
    context = "{path}/{repository}/".format(
        path=path_to_script, repository=repository)
    dockerfile = "{file}.Dockerfile".format(file=name)
    labels = {"version": "{date}".format(date=TODAY)}
    repository = "{user}/{repository}".format(user=USER, repository=repository)
    for target in targets:
        latest_tag = "{name}-{target}".format(name=name, target=target)
        build_push(context=context,
                   dockerfile=dockerfile,
                   repository=repository,
                   tag=latest_tag,
                   target=target,
                   labels=labels,
                   push=push)

        dated_tag = "{latest}-{date}".format(latest=latest_tag, date=TODAY)
        build_push(context=context,
                   dockerfile=dockerfile,
                   repository=repository,
                   tag=dated_tag,
                   target=target,
                   labels=labels,
                   push=push)


@click.command()
@click.option("--generate/--no-generate",
              default=True,
              help="Generate docker files.")
@click.option("--push/--no-push",
              default=False,
              help="Push generated images to DockerHub.")
@click.argument("image",
                type=click.Choice(list(IMAGES) + ['all']))
def main(generate, push, image):
    """Build the docker images."""
    if generate:
        gen.generate()

    builds = IMAGES
    if image != 'all':
        builds = {image: IMAGES[image]}

    for name in builds:
        repository = builds[name]["repository"]
        targets = builds[name]["targets"]
        update(repository=repository, name=name, targets=targets, push=push)


if __name__ == "__main__":
    main()
