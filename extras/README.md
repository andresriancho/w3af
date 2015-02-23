## w3af - Web application security scanner
Official docker image for [w3af](http://w3af.org/)

There are two different Docker images for w3af: `stable` and `unstable`. The
`stable` image is built from the `master` branch in the project repositories while
`unstable` is built from `develop`. Choose wisely, as usual unstable releases have
more features but also potential bugs.

## Usage

 * In order to use w3af's docker image you'll first have to
 [install docker](http://docs.docker.com/installation/)
 
 * Then run these commands, please notice that the first time these commands are
 run the script will download a docker image from the registry, which might take
 between 1 and 5 minutes depending on your internet connection speed:

```
git clone https://github.com/andresriancho/w3af.git
cd w3af/extras/scripts/
sudo ./w3af_console_docker
```

## Sharing data with the container

When starting w3af using the `w3af_console_docker` or `w3af_gui_docker` commands
the docker containers are started with two volumes which are mapped to your
home directory:

 * `~/.w3af/` from your host is mapped to `/root/.w3af/` in the container.
 This directory is mostly used by w3af to store scan profiles and internal data.
 
 * `~/w3af-shared` from your host is mapped to `/root/w3af-shared` in the container.
 Use this directory to save your scan results and provide input files to w3af.

## Updating w3af-docker installation

When you first run `sudo ./w3af_console_docker` the helper script downloaded the
latest available docker image for w3af. Since we're improving our scanner almost
every week, you might want to get the latest docker image by running:

```
sudo docker pull andresriancho/w3af
```

## Debugging the container

The container runs a SSH daemon, which can be used to both run the `w3af_console`
and `w3af_gui`. To connect to a running container use `root` as username and
`w3af` as password. Usually you don't need to worry about this, since the helper
scripts will connect to the container for you.

Another way to debug the container is to run the script with the `-d` flag: 
```
$ sudo ./w3af_console_docker -d
Warning: Permanently added '172.17.0.150' (ECDSA) to the list of known hosts.
root@a01aa9631945:~# 
```

## TODO

I still need to figure out (and add to this documentation) the best way for
users to be able to perform these tasks:
 
 * Passing parameters to the docker: scripts, profiles, dictionary files
   (how do I run ./w3af_console -s foo.w3af ?). I believe that the helper script
   would have to "forward" the parameters to the docker run command.
 * [Run the GUI environment](http://stackoverflow.com/questions/16296753/can-you-run-gui-apps-in-a-docker)
 * Make the image smaller (docker-stash?)
 * Add docker usage to our official documentation at docs.w3af.org

