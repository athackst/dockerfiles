#!/usr/bin/env python3
"""Generate the dockerfiles from a jinja template."""
import ruamel.yaml
import json
import logging
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
            distro["compose_out_file"] = \
                f"docker-compose/{repository}/{name}-docker-compose.yml"
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


def generate_dockerfiles(log):
    """Generate the dockerfiles for this repo."""
    file_loader = FileSystemLoader("template")
    env = Environment(loader=file_loader)

    for dockerfile in templates.dockerfile_settings():
        # The jinja template
        template = env.get_template(dockerfile["template_file"])
        output = template.render(dockerfile)
        out_file = dockerfile["out_file"]
        log.info(f"Generating {out_file}")
        dockerfile_out = open(out_file, "w")
        dockerfile_out.write(output)
        dockerfile_out.close()


def generate_readmes(log):
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
        readme_out = open(readme_file, "w")
        readme_out.write(readme_output)
        readme_out.close()


def generate_docker_compose(log):
    """Generate the docker compose files."""
    file_loader = FileSystemLoader("template")
    env = Environment(loader=file_loader)

    for compose_settings in templates.dockercompose_settings():
        template = env.get_template(compose_settings["compose_file"])
        output = template.render(compose_settings)
        out_file = compose_settings["compose_out_file"]
        log.info(f"Generating {out_file}")
        compose_out = open(out_file, "w")
        compose_out.write(output)
        compose_out.close()


def generate_docker_workflow(log):
    """Generate workflow with non-eol images."""
    log.info("Generating workflow file.")
    workflow_file = ".github/workflows/docker.yml"
    docker_workflow = None
    with open(workflow_file, 'r') as file:
        docker_workflow = yaml.load(file)
        docker_workflow["jobs"]["docker"]["strategy"]["matrix"] = {
            "include": templates.workflow_names()}
    with open(workflow_file, "w") as file:
        yaml.indent(mapping=2, sequence=4, offset=2)
        yaml.width = 4294967296  # A very large number
        yaml.dump(docker_workflow, file)


def generate_readme_workflow(log):
    """Generate docker readme file workflow."""
    workflow_file = ".github/workflows/docker_readme.yml"
    docker_workflow = None
    with open(workflow_file, "r") as file:
        docker_workflow = yaml.load(file)
        docker_workflow["jobs"]["readme"]["strategy"]["matrix"] = {
            "docker_repo": templates.repo_names()
        }

    with open(workflow_file, "w") as file:
        yaml.indent(mapping=2, sequence=4, offset=2)
        yaml.dump(docker_workflow, file)


def generate_tasks(log):
    """Generate tasks with non-eol images."""
    log.info("Generating tasks.")
    tasks_file = ".vscode/tasks.json"
    with open(tasks_file, "r") as file:
        tasks = json_parser.load(file)
        for input in tasks["inputs"]:
            if input["id"] == "build_name":
                input["options"] = templates.task_names() + ["all"]
    with open(tasks_file, "w") as file:
        json_parser.dump(tasks, file, indent=2)


if __name__ == "__main__":
    # Set up logger.
    log.setLevel(logging.INFO)
    formatter = logging.Formatter("%(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)

    generate_dockerfiles(log)
    generate_readmes(log)
    generate_docker_compose(log)
    generate_docker_workflow(log)
    generate_readme_workflow(log)
    generate_tasks(log)
    log.info("Finished generating dockerfiles.")
