Installation procedure
======================

Prerequisites
-------------

Make sure you have the following software ready before starting the installation:
 * Git client (``sudo apt-get install git``)
 * Python 2.7 (installed by default in most systems)

Installation
------------

.. code-block:: bash

    git clone git@github.com:andresriancho/w3af.git
    cd w3af/
    ./w3af_console
    . /tmp/w3af_dependency_install.sh


Let me explain what's going on there:
 * First we use ``git`` to download w3af's source code
 * Then we try to run the ``w3af_console`` command, which will most likely fail because of missing dependencies. This command will generate a helper script at ``/tmp/w3af_dependency_install.sh`` that when run will install all the required dependencies.
 * Dependencies are installed by running ``/tmp/w3af_dependency_install.sh``

The framework dependencies don't change too often, but don't be alarmed if after updating your installation ``w3af`` requires you to install new dependencies.

Supported platforms
-------------------

The framework should work on all Python supported platforms and has been tested in various Linux distributions, Mac OSX, FreeBSD and OpenBSD.

.. note::

   The platform used for development and running our continuous integration tests is Ubuntu 12.04 LTS and is the one where the software is more tested.

.. warning::

   While in theory you can install w3af in Microsoft Windows, we don't recommend nor support that installation process.

