#!/usr/bin/env python3
"""Generate the dockerfiles from a jinja template."""
import os
import ruamel.yaml
import json
import logging
import click
from jinja2 import Environment, FileSystemLoader


log = logging.getLogger(__name__)
json_parser = json
yaml = ruamel.yaml.YAML()
yaml.preserve_quotes = True


class Templates:
    """Accessor to the templates file."""

    def __init__(self):
        """Initialize with a cache the templates.yml file."""
        self._settings = None
        with open("templates.yml", "r") as file:
            self._settings = yaml.load(file)

    def raw(self) -> dict:
        """Get raw template settings.

        Returns:
            dict: template settings
        """
        return self._settings

    def dockerfile_settings(self, eol: bool = False) -> dict:
        """Get dockerfile generation settings.

        Args:
            eol (bool, optional): Include eol images. Defaults to False.

        Returns:
            dict: Repository generation settings
        """
        dockerfiles = []
        for repository in self._settings:
            for settings in self._settings[repository]:
                if not eol and "eol" in settings:
                    continue
                name = settings["name"]
                settings["template_file"] = f"{repository}.dockerfile.jinja"
                settings["out_file"] = f"{repository}/{name}.Dockerfile"
                dockerfiles.append(settings)
        return dockerfiles

    def dockercompose_settings(self, eol: bool = False) -> dict:
        """Get docker compose generation settings.

        Args:
            eol (bool, optional): Include eol images. Defaults to False.

        Returns:
            dict: Repository generation settings
        """
        docker_compose_files = []
        # Currently only gz has compose files
        repository = "gz"
        for distro in self._settings[repository]:
            if "eol" in distro and not eol:
                continue
            # TODO: Update to allow nvidia/cuda
            if "nvidia" in distro["base_image"]:
                continue
            name = distro["name"]
            distro["compose_file"] = f"{repository}.docker-compose.yml.jinja"
            distro["compose_out_file"] = (
                f"docker-compose/{repository}/{name}-docker-compose.yml"
            )
            docker_compose_files.append(distro)
        return docker_compose_files

    def images(self, eol: bool = False) -> dict:
        """Get dict of images and targets to build.

        Args:
            eol (bool, optional): Include eol images. Defaults to False.

        Returns:
            dict: images and targets
        """
        image_list = {}
        for repository in self._settings:
            for dockerfile in self._settings[repository]:
                if not eol and "eol" in dockerfile:
                    continue
                targets = list()
                for target in dockerfile["targets"]:
                    targets.append(target["target"])
                image_list[dockerfile["name"]] = {
                    "repository": repository,
                    "targets": targets,
                }
        return image_list

    def workflow_names(self, eol: bool = False) -> list:
        """List workflow docker images.

        Args:
            eol (bool, optional): Include eol images. Defaults to False.

        Returns:
            list: A list includes for github workflow
        """
        data = self._settings
        output = []

        for repo in data:
            for entry in data[repo]:
                tag = entry["name"]
                if not eol and "eol" in entry.keys():
                    continue

                for target in entry["targets"]:
                    item = {
                        "label": repo,
                        "tag": tag,
                        "target": target["target"],
                        "platforms": target["platforms"],
                    }
                    output.append(item)
        return output

    def task_names(self, eol: bool = False) -> list:
        """List workflow docker images.

        Args:
            eol (bool, optional): Include eol images. Defaults to False.

        Returns:
            list: A list of image names
        """
        image_list = []
        for repository in self._settings:
            for dockerfile in self._settings[repository]:
                if not eol and "eol" in dockerfile.keys():
                    continue
                image_list.append(dockerfile["name"])
        return image_list

    def repo_names(self) -> list:
        """List the docker repos.

        Returns:
            list: The docker repository names
        """
        return [repository for repository in self._settings]


templates = Templates()


def generate_dockerfiles(eol: bool = False):
    """Generate the dockerfiles for this repo."""
    file_loader = FileSystemLoader("template")
    env = Environment(loader=file_loader)

    for dockerfile in templates.dockerfile_settings(eol=eol):
        # The jinja template
        template = env.get_template(dockerfile["template_file"])
        output = template.render(dockerfile)
        out_file = dockerfile["out_file"]
        log.info(f"Generating {out_file}")
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        dockerfile_out = open(out_file, "w")
        dockerfile_out.write(output)
        dockerfile_out.close()


def generate_readmes():
    """Generate the readme files."""
    file_loader = FileSystemLoader("template")
    env = Environment(loader=file_loader)
    repositories = templates.repo_names()
    for repository in repositories:
        dockerfiles = templates.raw()[repository]
        log.info("Generating readme for {}".format(repository))
        readme_template = env.get_template("readme.md.jinja")
        readme_output = readme_template.render(
            {"repo_name": repository, "dockerfiles": dockerfiles}
        )
        readme_file = f"{repository}/README.md"
        os.makedirs(os.path.dirname(readme_file), exist_ok=True)
        readme_out = open(readme_file, "w")
        readme_out.write(readme_output)
        readme_out.close()


def generate_docker_compose(eol: bool = False):
    """Generate the docker compose files."""
    file_loader = FileSystemLoader("template")
    env = Environment(loader=file_loader)

    for compose_settings in templates.dockercompose_settings(eol=eol):
        template = env.get_template(compose_settings["compose_file"])
        output = template.render(compose_settings)
        out_file = compose_settings["compose_out_file"]
        log.info(f"Generating {out_file}")
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        compose_out = open(out_file, "w")
        compose_out.write(output)
        compose_out.close()


def generate_tasks(eol: bool = False):
    """Generate tasks with available image names."""
    log.info("Generating tasks.")
    tasks_file = ".vscode/tasks.json"
    with open(tasks_file, "r") as file:
        tasks = json_parser.load(file)
        for input in tasks["inputs"]:
            if input["id"] == "build_name":
                input["options"] = templates.task_names(eol=eol) + ["all"]
    with open(tasks_file, "w") as file:
        json_parser.dump(tasks, file, indent=2)


def generate_bake(include_eol=False):
    """Generate docker-bake.hcl from templates.yml."""
    file_loader = FileSystemLoader("template")
    env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)

    template = env.get_template("docker-bake.hcl.jinja")

    # Use the same source your other generators use
    data = templates.raw()

    output = template.render(
        settings=data,
        include_eol=include_eol,  # keep false to omit EOL entries
    )

    out_file = "docker-bake.hcl"
    log.info(f"Generating {out_file}")
    with open(out_file, "w") as f:
        f.write(output)


def gen(log, eol: bool = False):
    log = log
    generate_dockerfiles(eol=eol)
    generate_readmes()
    generate_docker_compose(eol=eol)
    generate_tasks(eol=eol)


def setup_logging():
    # Set up logger.
    log.setLevel(logging.INFO)
    formatter = logging.Formatter("%(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)


@click.command()
@click.option(
    "--eol/--no-eol",
    default=False,
    help="Include end-of-life images when generating files.",
)
def main(eol: bool):
    """Generate Dockerfiles, compose files, readmes, and task entries."""
    setup_logging()
    gen(log, eol=eol)
    generate_bake(include_eol=eol)
    log.info("Finished generating dockerfiles.")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
