#!/usr/bin/env python3
"""Settings to generate docker images."""


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
                'name': 'dome',
                'ubuntu_distro': '18.04',
                'ign_distro': 'dome',
                'gazebo_version': '3'
            },
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
        ],
        'github': [
            {
                'name': 'pages'
            }
        ]
    }


def targets():
    """List of default targets for the dockerfiles."""
    return ["base", "dev", "full", "gazebo"]


def images():
    """List of images and build settings."""
    return {
        "kinetic": {
            "repository": "ros",
            "targets": targets()
        },
        "melodic": {
            "repository": "ros",
            "targets": targets()
        },
        "noetic": {
            "repository": "ros",
            "targets": targets()
        },
        "dashing": {
            "repository": "ros2",
            "targets": targets()
        },
        "eloquent": {
            "repository": "ros2",
            "targets": targets()
        },
        "foxy": {
            "repository": "ros2",
            "targets": targets() + ["gazebo-nvidia"]
        },
        "gazebo10": {
            "repository": "gazebo",
            "targets": ["base", "dev"]
        },
        "gazebo11": {
            "repository": "gazebo",
            "targets": ["base", "dev", "nvidia"]
        },
        "blueprint": {
            "repository": "ignition",
            "targets": ["base", "dev"]
        },
        "citadel": {
            "repository": "ignition",
            "targets": ["base", "dev"]
        },
        "dome": {
            "repository": "ignition",
            "targets": ["base", "dev", "nvidia"]
        },
        "pages": {
            "repository": "github",
            "targets": ["dev"]
        },
    }
