w3af inside docker
==================

Using ``w3af`` inside docker should be transparent for most use cases, this page
documents the use cases which are complex to solve when docker is added to the
mix.

Ports and services
------------------

Some w3af plugins, such as ``crawl.spider_man`` and ``audit.rfi`` start proxy
HTTP services. In order to access these services the plugins need to be
configured to listen on ``0.0.0.0`` and the port needs to be made accessible
to the host using the ``-p`` parameter in the helper script
(ie. ``extras/docker/scripts/w3af_console_docker``)

Take a look at `this commit <https://github.com/andresriancho/w3af/commit/a8e2f66e31d8ad4a769cd0e7c12c87559dd026f3>`_
for more information about exposing ports.

Sharing data with the container
-------------------------------

When starting w3af using the ``w3af_console_docker`` or ``w3af_gui_docker``
commands the docker containers are started with two volumes which are mapped to
your home directory:

 * ``~/.w3af/`` from your host is mapped to ``/root/.w3af/`` in the container.
   This directory is mostly used by ``w3af`` to store scan profiles and internal
   data.

 * ``~/w3af-shared`` from your host is mapped to ``/root/w3af-shared`` in the
   container. Use this directory to save your scan results and provide input files
   to w3af.

Debugging the container
-----------------------

The container runs a SSH daemon, which can be used to both run the ``w3af_console``
and ``w3af_gui``. To connect to a running container use ``root`` as username and
``w3af`` as password. Usually you don't need to worry about this, since the helper
scripts will connect to the container for you.

Another way to debug the container is to run the script with the ``-d`` flag:

.. code-block:: console

    $ sudo ./w3af_console_docker -d
    root@a01aa9631945:~#


.. note::

    *WARNING*: Don't bind w3af's docker image to a public IP address unless you
    really know what you're doing! Anyone will be able to SSH into the docker
    image using the hard-coded SSH keys!
