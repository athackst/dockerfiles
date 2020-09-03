#!/usr/bin/env python3
"""Generate the dockerfiles from a jinja template."""
from jinja2 import Environment, FileSystemLoader
import logging

log = logging.getLogger(__name__)


def templates():
    """Dictionary of dockerfile templates and settings."""
    return {
        'ros2': [
            {
                'name': 'foxy',
                'ubuntu_distro': '20.04',
                'ros_distro': 'foxy',
                'python_version': '3.8'
            },
            {
                'name': 'eloquent',
                'ubuntu_distro': '18.04',
                'ros_distro': 'eloquent',
                'python_version': '3.6'
            },
            {
                'name': 'dashing',
                'ubuntu_distro': '18.04',
                'ros_distro': 'dashing',
                'python_version': '3.6'
            },
            {
                'name': 'crystal',
                'ubuntu_distro': '16.04',
                'ros_distro': 'crystal',
                'python_version': '3.6'
            },
        ],
        'ros': [
            {
                'name': 'noetic',
                'ubuntu_distro': '20.04',
                'ros_distro': 'noetic',
                'python_version': '3',
                'python_env': '3'
            },
            {
                'name': 'melodic',
                'ubuntu_distro': '18.04',
                'ros_distro': 'melodic',
                'python_version': '2.7',
                'python_env': ''
            },
            {
                'name': 'kinetic',
                'ubuntu_distro': '16.04',
                'ros_distro': 'kinetic',
                'python_version': '2.7',
                'python_env': ''
            }
        ],
        'ignition': [
            {
                'name': 'citadel',
                'ubuntu_distro': '18.04',
                'ign_distro': 'citadel',
                'gazebo_version': '3'
            },
            {
                'name': 'blueprint',
                'ubuntu_distro': '18.04',
                'ign_distro': 'blueprint',
                'gazebo_version': '2'
            },
        ],
        'gazebo': [
            {
                'name': 'gazebo11',
                'ubuntu_distro': '20.04',
                'gazebo_release': '11'
            },
            {
                'name': 'gazebo10',
                'ubuntu_distro': '18.04',
                'gazebo_release': '10'
            },
        ]
    }


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
