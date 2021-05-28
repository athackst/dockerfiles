#!/usr/bin/env python3
"""Settings to generate docker images."""


def templates():
    """Dictionary of dockerfile templates and settings."""
    return {
        'ros2': [
            {
                'name': 'galactic',
                'ubuntu_distro': '20.04',
                'ros_distro': 'galactic',
                'python_version': '3.8',
                'targets': ["base", "dev", "full", "gazebo", "gazebo-nvidia"]
            },
            {
                'name': 'foxy',
                'ubuntu_distro': '20.04',
                'ros_distro': 'foxy',
                'python_version': '3.8',
                'targets': ["base", "dev", "full", "gazebo", "gazebo-nvidia"]
            },
            {
                'name': 'dashing',
                'ubuntu_distro': '18.04',
                'ros_distro': 'dashing',
                'python_version': '3.6',
                'targets': ["base", "dev", "full", "gazebo"]
            },
        ],
        'ros': [
            {
                'name': 'noetic',
                'ubuntu_distro': '20.04',
                'ros_distro': 'noetic',
                'python_version': '3',
                'python_env': '3',
                'targets': ["base", "dev", "full", "gazebo"]
            },
            {
                'name': 'melodic',
                'ubuntu_distro': '18.04',
                'ros_distro': 'melodic',
                'python_version': '2.7',
                'python_env': '',
                'targets': ["base", "dev", "full", "gazebo"]
            },
            {
                'name': 'kinetic',
                'ubuntu_distro': '16.04',
                'ros_distro': 'kinetic',
                'python_version': '2.7',
                'python_env': '',
                'targets': ["base", "dev", "full", "gazebo"]
            }
        ],
        'ignition': [
            {
                'name': 'dome',
                'ubuntu_distro': '18.04',
                'ign_distro': 'dome',
                'gazebo_version': '3',
                "targets": ["base", "dev", "nvidia"]
            },
            {
                'name': 'citadel',
                'ubuntu_distro': '18.04',
                'ign_distro': 'citadel',
                'gazebo_version': '3',
                "targets": ["base", "dev", "nvidia"]
            },
            {
                'name': 'edifice',
                'ubuntu_distro': '20.04',
                'ign_distro': 'edifice',
                'gazebo_version': '3',
                "targets": ["base", "dev", "nvidia"]
            },
        ],
        'gazebo': [
            {
                'name': 'gazebo11',
                'ubuntu_distro': '20.04',
                'gazebo_release': '11',
                "targets": ["base", "dev", "nvidia"]
            },
            {
                'name': 'gazebo9',
                'ubuntu_distro': '18.04',
                'gazebo_release': '9',
                "targets": ["base", "dev"]
            },
        ],
        'github': [
            {
                'name': 'pages',
                "targets": ["dev"]
            }
        ]
    }


def images():
    """List of images and targets."""
    image_list = {}
    for repository in templates():
        for dockerfile in templates()[repository]:
            image_list[dockerfile["name"]] = {
                "repository": repository,
                "targets": dockerfile["targets"]
            }
    return image_list
