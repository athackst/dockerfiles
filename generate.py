#!/usr/bin/env python3
"""Generate the dockerfiles from a jinja template."""
import ruamel.yaml
import json
import logging
from datetime import datetime
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

        # Set EOL status based on 'eol' or 'eol_date' at initialization.
        self._process_eol_status()

    def _process_eol_status(self):
        """Update settings with EOL status based on the date or 'eol' field."""
        today = datetime.today().date()

        for repository in self._settings:
            for dockerfile in self._settings[repository]:
                # If 'eol' is already explicitly set, keep it.
                if "eol" in dockerfile:
                    continue

                # Otherwise, calculate EOL status based on 'eol_date'.
                if "eol_date" in dockerfile:
                    eol_date = datetime.strptime(
                        dockerfile["eol_date"], "%Y-%m-%d").date()
                    # True if the date has passed.
                    dockerfile["eol"] = today > eol_date
                else:
                    # Default to False if no date is given.
                    dockerfile["eol"] = False

    def raw(self) -> dict:
        """Get raw template settings.

        Returns:
            dict: template settings
        """
        return self._settings

    def dockerfile_settings(self, include_eol: bool = False) -> dict:
        """Get dockerfile generation settings.

        Args:
            eol (bool, optional): Include eol images. Defaults to False.

        Returns:
            dict: Repository generation settings
        """
        dockerfiles = []
        for repository in self._settings:
            for settings in self._settings[repository]:
                if not include_eol and settings["eol"]:
                    continue
                name = settings["name"]
                settings["template_file"] = f"{repository}.dockerfile.jinja"
                settings["out_file"] = f"{repository}/{name}.Dockerfile"
                dockerfiles.append(settings)
        return dockerfiles

    def images(self, include_eol: bool = False) -> dict:
        """Get dict of images and targets to build.

        Args:
            eol (bool, optional): Include eol images. Defaults to False.

        Returns:
            dict: images and targets
        """
        image_list = {}
        for repository in self._settings:
            for dockerfile in self._settings[repository]:
                if not include_eol and dockerfile["eol"]:
                    continue
                targets = list()
                for target in dockerfile["targets"]:
                    targets.append(target["target"])
                image_list[dockerfile["name"]] = {
                    "repository": repository,
                    "targets": targets,
                }
        return image_list

    def workflow_names(self, include_eol: bool = False) -> list:
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
                if not include_eol and entry["eol"]:
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

    def task_names(self, include_eol: bool = False) -> list:
        """List workflow docker images.

        Args:
            eol (bool, optional): Include eol images. Defaults to False.

        Returns:
            list: A list of image names
        """
        image_list = []
        for repository in self._settings:
            for dockerfile in self._settings[repository]:
                if not include_eol and dockerfile["eol"]:
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
    env = Environment(loader=FileSystemLoader("template"))

    for dockerfile in templates.dockerfile_settings():
        template = env.get_template(dockerfile["template_file"])
        output = template.render(dockerfile)
        out_file = dockerfile["out_file"]

        log.info(f"Generating {out_file}")
        with open(out_file, "w") as f:
            f.write(output)


def generate_readmes(log):
    """Generate the readme files."""
    env = Environment(loader=FileSystemLoader("template"))

    for repository in templates.repo_names():
        dockerfiles = templates.raw()[repository]
        log.info(f"Generating readme for {repository}")
        
        readme_template = env.get_template("readme.md.jinja")
        readme_output = readme_template.render(
            {"repo_name": repository, "dockerfiles": dockerfiles}
        )

        readme_file = f"{repository}/README.md"
        with open(readme_file, "w") as f:
            f.write(readme_output)


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
    generate_docker_workflow(log)
    generate_readme_workflow(log)
    generate_tasks(log)
    log.info("Finished generating dockerfiles.")
