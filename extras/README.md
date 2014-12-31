## w3af - Web application security scanner
Official docker image for [w3af](http://w3af.org/)

There are two different Docker images for w3af: `stable` and `unstable`. The
`stable` image is built from the `master` branch in the project repositories while
`unstable` is built from `develop`. Choose wisely, as usual unstable releases have
more features but also potential bugs.

## Usage

TODO

## SSH connection

The container runs a SSH daemon, which can be used to both run the `w3af_console`
and `w3af_gui`. To connect to a running container use `root` as username and
`w3af` as password. Usually you don't need to worry about this, since the helper
scripts will connect to the container for you.

## Sharing data with the container

When starting w3af using the `w3af_console_docker` or `w3af_gui_docker` commands
the docker containers are started with two volumes which are mapped to your
home directory:

 * `~/.w3af/` from your host is mapped to `/home/w3af/.w3af/` in the container.
 This directory is mostly used by w3af to store scan profiles and internal data.
 
 * `~/w3af-shared` from your host is mapped to `/home/w3af/w3af-shared` in the container.
 Use this directory to save your scan results and provide input files to w3af.

## Docker
[Docker basics](https://www.docker.com/tryit/) and
[installation](http://docs.docker.com/installation/) is out of the scope of
this documentation, but follow the links to get started.  

## TODO

I still need to figure out (and add to this documentation) the best way for
users to be able to perform these tasks:

 * Save scan results to the host file system (most likely using [docker volumes](https://docs.docker.com/userguide/dockervolumes/))  
 * Passing parameters to the docker: scripts, profiles, dictionary files (how do I run ./w3af_console -s foo.w3af when foo.w3af is in the host system?) (most likely using [docker volumes](https://docs.docker.com/userguide/dockervolumes/))
 * The user needs to accept the terms and conditions each time he runs the docker image, that's annoying. I would like him to accept them only once.  
 * [Run the GUI environment](http://stackoverflow.com/questions/16296753/can-you-run-gui-apps-in-a-docker)
 This works now.  It requires more commands at the moment, but we're working on that little bit of inconvenience.  The release path looks like:  
 * Make the image smaller
 * Add docker usage to our official documentation at docs.w3af.org

