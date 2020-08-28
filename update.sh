#!/bin/bash
set -e

push=0
TODAY=$(date +'%Y-%m-%d')

update() {
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

update_crystal() {
  read -p "WARNING: Updating EOL distribution. Are you sure? (y/n)" -n 1 -r
  if [[ $REPLY =~ ^[Yy]$ ]]
  then
    docker pull ubuntu:16.04
    update ros2 crystal base
    update ros2 crystal dev
  fi
}

update_pages() {
  docker pull jekyll/jekyll:pages
  update github pages dev
}

update_dashing() {
  docker pull ubuntu:18.04
  update ros2 dashing base
  update ros2 dashing dev
  update ros2 dashing full
}

update_eloquent() {
  docker pull ubuntu:18.04
  update ros2 eloquent base
  update ros2 eloquent dev
  update ros2 eloquent full
}

update_foxy() {
  docker pull ubuntu:20.04
  update ros2 foxy base
  update ros2 foxy dev
  update ros2 foxy full
}

update_kinetic() {
  docker pull ubuntu:18.04
  update ros kinetic base
  update ros kinetic dev
  update ros kinetic full
}

update_melodic() {
  docker pull ubuntu:18.04
  update ros melodic base
  update ros melodic dev
  update ros melodic full
}

update_noetic() {
  docker pull ubuntu:20.04
  update ros noetic base
  update ros noetic dev
  update ros noetic full
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
