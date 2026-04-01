#!/usr/bin/env python3
"""Generate the dockerfiles from a jinja template."""
import os
import json
import logging
import click
from jinja2 import Environment, FileSystemLoader
from dockerfiles_templates import Templates


log = logging.getLogger(__name__)
json_parser = json
templates = Templates()


def generate_dockerfiles(eol: bool = False):
    """Generate the dockerfiles for this repo."""
    file_loader = FileSystemLoader("template")
    env = Environment(loader=file_loader)
    entries = templates.entries(eol=eol)

    for entry in entries:
        settings = entry.copy()
        family = settings["family"]
        name = settings["name"]
        settings["template_file"] = f"{family}.dockerfile.jinja"
        settings["out_file"] = f"{family}/{name}.Dockerfile"
        template_file = f"{family}.dockerfile.jinja"
        out_file = f"{family}/{name}.Dockerfile"
        # The jinja template
        template = env.get_template(template_file)
        output = template.render(settings)
        log.info(f"Generating {out_file}")
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        dockerfile_out = open(out_file, "w")
        dockerfile_out.write(output)
        dockerfile_out.close()


def generate_readmes():
    """Generate the readme files."""
    file_loader = FileSystemLoader("template")
    env = Environment(loader=file_loader)
    repositories = templates.group_by("family").keys()
    for repository in repositories:
        dockerfiles = templates.entries(family=repository, eol=True)
        dockerfiles_for_readme = []
        for dockerfile in dockerfiles:
            dockerfile_out = dockerfile.copy()
            dockerfile_out["in_eol"] = templates.is_past_eol(dockerfile)
            dockerfiles_for_readme.append(dockerfile_out)

        if not dockerfiles_for_readme:
            continue
        log.info("Generating readme for {}".format(repository))
        readme_template = env.get_template("readme.md.jinja")
        readme_output = readme_template.render(
            {"repo_name": repository, "dockerfiles": dockerfiles_for_readme}
        )
        readme_file = f"{repository}/README.md"
        os.makedirs(os.path.dirname(readme_file), exist_ok=True)
        readme_out = open(readme_file, "w")
        readme_out.write(readme_output)
        readme_out.close()


def get_compose_templates():
    """Get docker compose templates from templates folder."""
    suffix = ".docker-compose.yml.jinja"
    compose_templates = []
    for entry in os.scandir("template"):
        if not entry.is_file() or not entry.name.endswith(suffix):
            continue
        prefix = entry.name[: -len(suffix)]
        parts = prefix.split(".", 1)
        if len(parts) != 2:
            continue
        group, family = parts
        compose_templates.append(
            {
                "family": family,
                "group": group,
                "file": entry.name,
            }
        )
    return compose_templates


def generate_docker_compose(eol: bool = False):
    """Generate the docker compose files."""
    file_loader = FileSystemLoader("template")
    env = Environment(loader=file_loader)

    compose_templates = get_compose_templates()

    for compose_template in compose_templates:
        group = compose_template["group"]
        family = compose_template["family"]
        template_file = compose_template["file"]
        log.info(f"Template file: {template_file}")
        template = env.get_template(template_file)
        entries = templates.entries(family=family, eol=eol)
        for entry in entries:
            name = entry["name"]
            output = template.render(entry)
            out_file = f"docker-compose/{group}/{name}-docker-compose.yml"
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
                input["options"] = templates.image_tokens(eol=eol)
    with open(tasks_file, "w") as file:
        json_parser.dump(tasks, file, indent=2)
        file.write("\n")


def generate_bake():
    """Generate docker-bake.hcl from templates.yml.

    Bake always includes all configured targets (including EOL). EOL filtering
    is handled by selection logic elsewhere (build/workflows).
    """
    file_loader = FileSystemLoader("template")
    env = Environment(loader=file_loader, trim_blocks=True, lstrip_blocks=True)

    template = env.get_template("docker-bake.hcl.jinja")

    # Always emit all bake targets/groups, but keep default as non-EOL.
    all_settings = templates.group_by("family", eol=True)
    active_settings = templates.group_by("family", eol=False)

    output = template.render(
        settings=all_settings,
        active_settings=active_settings,
        include_eol=True,
    )

    out_file = "docker-bake.hcl"
    log.info(f"Generating {out_file}")
    with open(out_file, "w") as f:
        f.write(output)


def gen(log, eol: bool = False):
    """Run all generation steps for dockerfiles, readmes, compose, and tasks."""
    log = log
    generate_dockerfiles(eol=eol)
    generate_readmes()
    generate_docker_compose(eol=eol)
    generate_bake()
    generate_tasks(eol=eol)


def setup_logging():
    """Configure logger output for generation scripts."""
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
    help="Include expired end-of-life images too.",
)
def main(eol: bool):
    """Generate Dockerfiles, compose files, readmes, and task entries."""
    setup_logging()
    gen(log, eol=eol)
    log.info("Finished generating dockerfiles.")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
