## w3af - Web application security scanner
Official docker image for [w3af](http://w3af.org/)

There are two different Docker images for w3af: `stable` and `unstable`. The `stable` image is built from the `master` branch in the project repositories while `unstable` is built from `develop`. Choose wisely, as usual unstable releases have more features but also potential bugs.

Note: The recent changes make it more complex to launch w3af, but it's something on which we're working.  It should all be automated shortly.

## Usage

First you'll have to get the image (see the note above on stable and unstable releases):

```bash
docker pull andresriancho/w3af:unstable
```

And then run the docker instance to generate a container:

```bash
docker run -d --name w3af andresriancho/w3af:unstable
```

Naming all the things makes it easier to automate the other things later on.  

## Docker
[Docker basics](https://www.docker.com/tryit/) and [installation](http://docs.docker.com/installation/) is out of the scope of this documentation, but follow the links to get started.  

For now, you have do `docker inspect w3af | grep IPAddr` and `ssh -X root@ip-addr` enter w3af as password to get in to the container.  This will be automated later.

## TODO

I still need to figure out (and add to this documentation) the best way for users to be able to perform these tasks:

 * Save scan results to the host file system (most likely using [docker volumes](https://docs.docker.com/userguide/dockervolumes/))  
 There is volume mapping built in to the next patch, but it isn't ready for general consumption yet.  
 * Passing parameters to the docker: scripts, profiles, dictionary files (how do I run ./w3af_console -s foo.w3af when foo.w3af is in the host system?) (most likely using [docker volumes](https://docs.docker.com/userguide/dockervolumes/))
There is volume mapping built in to the next patch, but it isn't ready for general consumption yet.  
  * The user needs to accept the terms and conditions each time he runs the docker image, that's annoying. I would like him to accept them only once.
This can be accomplished with either using `docker commit w3af` on the local installation from a terminal while the instance is still running or with a shared .w3af folder.  The first one works now.  The latter one will work later.  

 * [Run the GUI environment](http://stackoverflow.com/questions/16296753/can-you-run-gui-apps-in-a-docker)
 This works now.  It requires more commands at the moment, but we're working on that little bit of inconvenience.  The release path looks like:  
Get docker GUI container working. - done  
Get helper scripts working to launch w3af docker in a single command.  
Get helper and core scripts to use shared folders.  
Get helper scripts working to pass all this through boot2docker, so we only have one dependency hell to troubleshoot instead of three.  

 * Make the image smaller
 * Add docker usage to our official documentation at docs.w3af.org

