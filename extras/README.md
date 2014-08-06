## w3af - Web application security scanner
Official docker image for [w3af](http://w3af.org/)

There are two different Docker images for w3af: `stable` and `unstable`. The `stable` image is built from the `master` branch in the project repositories while `unstable` is built from `develop`. Choose wisely, as usual unstable releases have more features but also potential bugs.

## Usage

First you'll have to get the image (see the note above on stable and unstable releases):

```bash
sudo docker pull andresriancho/w3af:unstable
```

And then run the docker:

```bash
sudo docker run --interactive --tty andresriancho/w3af:unstable
```

## Docker
[Docker basics](https://www.docker.com/tryit/) and [installation](http://docs.docker.com/installation/) is out of the scope of this documentation, but follow the links to get started.

## TODO

I still need to figure out (and add to this documentation) the best way for users to be able to perform these tasks:

 * Save scan results to the host file system
 * Passing parameters to the docker: scripts, profiles, dictionary files (how do I run ./w3af_console -s foo.w3af when foo.w3af is in the host system?)
  * The user needs to accept the terms and conditions each time he runs the docker image, that's annoying. I would like him to accept them only once.

