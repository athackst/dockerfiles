#!/usr/bin/env python3
"""Generate the dockerfiles from a jinja template."""
from jinja2 import Environment, FileSystemLoader

TEMPLATES = {
    'ros2': [
        {
            'ubuntu_distro': '20.04',
            'ros_distro': 'foxy',
            'python_version': 3.8
        },
        {
            'ubuntu_distro': '18.04',
            'ros_distro': 'eloquent',
            'python_version': 3.6
        },
        {
            'ubuntu_distro': '18.04',
            'ros_distro': 'dashing',
            'python_version': 3.6
        },
        {
            'ubuntu_distro': '16.04',
            'ros_distro': 'crystal',
            'python_version': 3.6
        },
    ],
    'ros': [
        {
            'ubuntu_distro': '20.04',
            'ros_distro': 'noetic',
            'python_version': 3,
            'python_env': 3
        },
        {
            'ubuntu_distro': '18.04',
            'ros_distro': 'melodic',
            'python_version': 2.7,
            'python_env': 2
        },
        {
            'ubuntu_distro': '16.04',
            'ros_distro': 'kinetic',
            'python_version': 2.7,
            'python_env': 2
        }
    ]
}


def generate():
    """Generate the dockerfiles for this repo."""
    file_loader = FileSystemLoader('template')
    env = Environment(loader=file_loader)

    for name in TEMPLATES:
        template_name = name + ".dockerfile.jinja"
        dockerfiles = TEMPLATES[name]
        template = env.get_template(template_name)
        for file in dockerfiles:
            output = template.render(file)
            out_file = name + "/" + file['ros_distro'] + ".Dockerfile"
            print("Generating {filename}".format(filename=out_file))
            dockerfile_out = open(out_file, "w")
            dockerfile_out.write(output)
            dockerfile_out.close()


if __name__ == "__main__":
    # execute only if run as a script
    generate()
    print("Finished generating dockerfiles.")
