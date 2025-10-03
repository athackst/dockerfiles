#!/usr/bin/env python3
"""Update script for dockerfiles."""
import os
import click
import logging
from datetime import date
from generate import templates
from generate import generate_dockerfiles as gen

TODAY = date.today()
USER = "althack"

log = logging.getLogger(__name__)


def should_push():
    """Set whether or not to push from environment variables.

    Env:
        push: $DOCKER_PUSH
    """
    return os.getenv("DOCKER_PUSH")


def should_clean():
    """Set whether or not to clean images from environment variables.

    Env:
        push: $DOCKER_CLEAN
    """
    return os.getenv("DOCKER_CLEAN")


class Docker(object):
    """Managed docker class to hide complexity with logging output."""

    def __init__(self):
        """Initialize docker container from environment."""

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
        build_tag = f"{repository}:{tag}"
        log.info(f"Building {context}{dockerfile} {target} as {build_tag}")
        dockerfile = os.path.join(context, dockerfile)
        ret = os.system(
            f"docker build "
            f"--file {dockerfile} "
            f"--target {target} "
            f"--tag {build_tag} "
            f"--pull {context}"
        )
        if ret != 0:
            raise Exception("Error building docker image")
        log.info(f"Done building {build_tag}")

    def tag(self, repository, prev_tag, new_tag):
        """Tag a built image."""
        image = f"{repository}:{prev_tag}"
        log.info(f"Taging {image} --> {repository}:{new_tag}")
        ret = os.system(f"docker tag {image} {repository}:{new_tag}")
        if ret != 0:
            raise Exception("Error tagging docker image")

    def push(self, repository, tag):
        """Push a built repository:tag to a registry.

        Format: repository:tag

        Args:
            repository: The name of the repository.
            tag: The name of the tag.
        """
        log.info(f"Pushing {repository}:{tag}")
        ret = os.system(f"docker push {repository}:{tag}")
        if ret != 0:
            raise Exception("Error pushing docker image")

        log.info(f"Done pushing {repository}:{tag}")

    def prune(self):
        """Prune dangling images."""
        ret = os.system("docker system prune -f")
        if ret != 0:
            raise Exception("Error pruning docker images")

    def rmi(self, repository, tag):
        """Remove image by repository and tag."""
        image = f"{repository}:{tag}"
        ret = os.system(f"docker rmi {image}")
        if ret != 0:
            raise Exception("Error removing docker image")


def build(image, target, push, clean):
    """Build the docker images."""
    builds = templates.images(eol=True)
    if image != "all":
        builds = {image: templates.images()[image]}

    # Build docker images.
    dockerpy = Docker()
    path_to_script = os.path.dirname(os.path.abspath(__file__))
    for name in builds:
        folder = builds[name]["repository"]
        repository = f"{USER}/{folder}"
        targets = builds[name]["targets"] if not target else [target]
        context = f"{path_to_script}/{folder}/"
        dockerfile = f"{name}.Dockerfile"
        labels = {"version": f"{TODAY}"}
        for target in targets:
            latest_tag = f"{name}-{target}"
            dated_tag = f"{latest_tag}-{TODAY}"
            dockerpy.build(
                context=context,
                dockerfile=dockerfile,
                repository=repository,
                tag=latest_tag,
                target=target,
                labels=labels,
            )

            if push or should_push():
                dockerpy.push(repository=repository, tag=latest_tag)
                dockerpy.tag(
                    repository=repository,
                    prev_tag=latest_tag,
                    new_tag=dated_tag
                )
                dockerpy.push(repository=repository, tag=dated_tag)
                dockerpy.rmi(repository=repository, tag=dated_tag)
    if clean or should_clean():
        dockerpy.prune()


@click.command()
@click.option(
    "--generate/--no-generate", default=True, help="Generate docker files."
)
@click.option(
    "--push/--no-push",
    default=False,
    help="Push generated images to DockerHub.",
)
@click.option(
    "--clean/--no-clean",
    default=True,
    help="Clean dated content and old images.",
)
@click.option("--target", default="", help="The target to build")
@click.argument("image", type=click.Choice(list(templates.images()) + ["all"]))
def main(generate, push, clean, image, target):
    """Set up logging and trigger build."""
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(message)s")
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    log.addHandler(ch)

    if generate:
        gen(log)

    build(image, target, push, clean)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
