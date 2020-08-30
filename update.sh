#!/bin/bash
set -e

push=0
TODAY=$(date +'%Y-%m-%d')

_update() {
  # Update the base image
  USERNAME=athackst
  DOCKER_BASE_NAME=$1
  DOCKER_IMG_NAME=$2
  DOCKER_TARGET_NAME=$3
  DOCKER_FILE=${DOCKER_BASE_NAME}/${DOCKER_IMG_NAME}.Dockerfile
  LATEST_TAG=${DOCKER_IMG_NAME}-${DOCKER_TARGET_NAME}
  DATED_TAG=${LATEST_TAG}-${TODAY}

  REPOSITORY=${USERNAME}/${DOCKER_BASE_NAME}
  CONTEXT=${DOCKER_BASE_NAME}
  
  # first try to pull a remote image, if fail,
  docker build -f ${DOCKER_FILE} \
    --target ${DOCKER_TARGET_NAME} \
    -t ${REPOSITORY}:${LATEST_TAG} \
    -t ${REPOSITORY}:${DATED_TAG} \
    --label "version=${TODAY}" \
    ${CONTEXT}
  
  # Push the image to the remote.
  if [ "$push" = "1" ]; then
    docker login
    docker push ${REPOSITORY}:${LATEST_TAG}
    docker push ${REPOSITORY}:${DATED_TAG}
  fi
  
  docker rmi ${REPOSITORY}:${DATED_TAG}
  docker system prune -f
}

targets=( "base", "dev", "full", "gazebo")
_update_targets() {
  for target in "${targets[@]}"; do
    _update ${repo} ${distro} ${target}
  done
}

set_crystal() {
  read -p "WARNING: Updating EOL distribution. Are you sure? (y/n)" -n 1 -r
  if [[ $REPLY =~ ^[Yy]$ ]]
  then
    repo="ros2"
    distro="crystal"
    docker pull ubuntu:16.04
    _update_targets
  fi
}

update_dashing() {
  repo="ros2"
  distro="dashing"
  docker pull ubuntu:18.04
  _update_targets
}

update_eloquent() {
  repo="ros2"
  distro="eloquent"
  docker pull ubuntu:18.04
  _update_targets
}

update_foxy() {
  repo="ros2"
  distro="foxy"
  docker pull ubuntu:20.04
  _update_targets
}

update_kinetic() {
  repo="ros"
  distro="kinetic"
  docker pull ubuntu:18.04
  _update_targets
}

update_melodic() {
  repo="ros"
  distro="melodic"
  docker pull ubuntu:18.04
  _update_targets
}

update_noetic() {
  repo="ros"
  distro="noetic"
  docker pull ubuntu:20.04
  _update_targets
}

update_pages() {
  docker pull jekyll/jekyll:pages
  update github pages dev
}

update_all() {
  # this is the list of currently active ros releases
  update_dashing
  update_eloquent
  update_foxy
  update_kinetic
  update_melodic
  update_noetic
  update_pages
}

usage() {
  echo "usage: update.sh [[-p] [-h]] [[dashing|eloquent|foxy|kinetic|melodic|noetic|pages|all]]"
  echo " -p, --push                    : push the build to remote"
  echo " -h, --help                    : print this message"
  echo " <release> | all               : Update a particular release or all currently supported releases"
}

while [ "$1" != "" ]; do
  case $1 in
    -p | --push )
      push=1
    ;;
    -h | --help )
      usage
      exit
    ;;
    * )
      VERSION=$1
    ;;
  esac
  shift
done

if [ -z ${VERSION} ]; then
  usage
  exit
fi

update_${VERSION}
