#!/usr/bin/env python3

import subprocess
import re
import sys
from difflib import unified_diff

# List of known variable patterns to ignore (regex-supported)
IGNORE_PATTERNS = [
    r'^HOSTNAME=',
    r'^PWD=',
    r'^SHLVL=',
    r'^_='
]


def get_source_env_from_image(image, version):
    """Extract environment variables from a Docker image after sourcing."""
    result = subprocess.run(
        ["docker", "run", "--rm", image,
         "bash", "-c", f"source /opt/ros/{version}/setup.bash && env"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )
    return result.stdout.splitlines()


def get_env_from_image(image):
    """Extract environment variables from a Docker image."""
    result = subprocess.run(
        ["docker", "run", "--rm", image, "env"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True
    )
    return result.stdout.splitlines()


def filter_env(env_lines):
    """Filter out environment variables that match known patterns."""
    filtered = []
    for line in env_lines:
        if not any(re.match(pattern, line) for pattern in IGNORE_PATTERNS):
            filtered.append(line)
    return sorted(filtered)


def compare_envs(env1, env2):
    """Compare two sets of environment variables and print differences."""
    diff = list(unified_diff(env1, env2, fromfile='Base Image',
                tofile='New Image', lineterm=''))
    if diff:
        print("Environment differences detected:")
        for line in diff:
            print(line)
        sys.exit(1)
    else:
        print("Test passed: No unexpected changes in the environment.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: compare_env.py <image> <version>")
        sys.exit(1)

    image, version = sys.argv[1], sys.argv[2]

    print(f"Sourcing {version} and extracting environment from {image}...")
    base_env = get_source_env_from_image(image, version)

    print(f"Extracting environment from {image}...")
    new_env = get_env_from_image(image)

    print("Filtering known differences...")
    base_env_filtered = filter_env(base_env)
    new_env_filtered = filter_env(new_env)

    print("Comparing environments...")
    compare_envs(base_env_filtered, new_env_filtered)
