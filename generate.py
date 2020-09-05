#!/usr/bin/env python3
"""Generate the dockerfiles from a jinja template."""
from jinja2 import Environment, FileSystemLoader
from settings import templates
from settings import images
import logging

log = logging.getLogger(__name__)


def generate(log):
    """Generate the dockerfiles for this repo."""
    file_loader = FileSystemLoader('template')
    env = Environment(loader=file_loader)

    for name in templates():
        template_name = name + ".dockerfile.jinja"
        dockerfiles = templates()[name]
        template = env.get_template(template_name)
        for file in dockerfiles:
            output = template.render(file)
            out_file = name + "/" + file['name'] + ".Dockerfile"
            log.info("Generating {filename}".format(filename=out_file))
            dockerfile_out = open(out_file, "w")
            dockerfile_out.write(output)
            dockerfile_out.close()
        log.info("Generating readme for {name}".format(name=name))
        readme_template = env.get_template('readme.md.jinja')
        readme_output = readme_template.render(
            {"repo_name": name,
             "dockerfiles": dockerfiles,
             "images": images()})
        readme_file = name + "/README.md"
        readme_out = open(readme_file, "w")
        readme_out.write(readme_output)
        readme_out.close()


if __name__ == "__main__":
    # Set up logger.
    log.setLevel(logging.INFO)
    formatter = logging.Formatter('%(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    log.addHandler(ch)

    generate(log)
    log.info("Finished generating dockerfiles.")
