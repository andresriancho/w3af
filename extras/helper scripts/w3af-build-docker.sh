#!/usr/bin/env bash

function shared_folders_warning(){
  echo "Shared folder did not exist."
  echo "Ensure /opt/w3af/w3af-shared and /opt/w3af/.w3af exist"
  exit 2
}

function build_w3af_docker(){
  test=$(docker images | grep w3af)
  if [ "${#test}" -eq "0" ]; then
    #substitute pulling from dockerhub when the image clicks over to SSH enabled
  	cd ../dockerfile
  	docker build -t w3af-template .
  	cd -
  fi
  if [ ! -d "/opt/w3af/w3af-shared" ]; then
  	shared_folders_warning
  fi
  if [ ! -d "/opt/w3af/.w3af" ]; then
  	shared_folders_warning
  fi
  test=$(docker ps -a | grep w3af)
  #substitute the andres:w3af pull when it clicks over to ssh enabled.
  if [ "${#test}" -eq "0" ]; then
  	docker run -d --name w3af -v /opt/w3af/.w3af:/home/w3af/.w3af -v /opt/w3af/w3af-shared:/home/w3af/w3af-shared w3af-template
  fi
}

build_w3af_docker