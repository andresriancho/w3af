Advanced installation
=====================

.. warning::

   None of these installation methods are recommended for new users.
   Please refer to :doc:`install` for the most common ways to get started with ``w3af``.

Bleeding edge vs. stable
------------------------

We develop ``w3af`` using ``git flow``, this means that we'll always have at least
two branches in our repository:

 * ``master``: The branch where our latest stable code lives. We take it very
 seriously to make sure all unit tests ``PASS`` in this branch.
 * ``develop``: The branch where new features are merged and tested. Not as
 stable as ``master`` but we try to keep this one working too.

Advanced users might want to be on the bleeding edge aka ``develop`` to get the
latest features, while users using ``w3af`` for continuous scanning and other
tasks which require stability would choose ``master`` (our stable release).

Moving to bleeding edge ``w3af`` is easy:

.. code-block:: bash

    git clone https://github.com/andresriancho/w3af.git
    cd w3af/
    git checkout develop
    ./w3af_console
    . /tmp/w3af_dependency_install.sh

To the regular installation procedure we added the ``git checkout develop``,
that's it! If you're running in this branch and find an issue, please report
it back to us too. We're interested in hearing about **any issues** users identify.

Installing using virtualenv
---------------------------

.. note::

   Installing in a ``virtualenv`` is great to isolate ``w3af`` python packages
   from the system packages.

Virtualenv is a great tool that will allow you to install ``w3af`` in a virtual
and isolated environment that won't affect your operating system python packages.

.. code-block:: console

    $ cd w3af
    $ virtualenv venv
    $ . venv/bin/activate
    (venv)$ ./w3af_console
    (venv)$ . /tmp/w3af_dependency_install.sh

All the packages installed using the ``/tmp/w3af_dependency_install.sh`` script
will be stored inside the ``venv`` directory and won't affect your system packages.

Installation of the GUI dependencies inside a ``virtualenv`` is a little bit
trickier since it requires C libraries which are not installed using ``pip``.
`This <http://stackoverflow.com/a/12831223/1347554>`_ information might be useful
for installing ``w3af``'s GUI inside a virtualenv:

.. code-block:: console

    $ cd w3af
    $ sudo apt-get install python-gtksourceview2 python-gtk2
    $ virtualenv --system-site-packages venv
    $ . venv/bin/activate
    (venv)$ ./w3af_gui
    (venv)$ . /tmp/w3af_dependency_install.sh

Or,

.. code-block:: console

    $ cd w3af
    $ sudo apt-get install python-gtksourceview2 python-gtk2
    $ virtualenv venv
    $ mkdir -p venv/lib/python2.7/dist-packages/
    $ cd venv/lib/python2.7/dist-packages/
    $ ln -s /usr/lib/python2.7/dist-packages/glib/ glib
    $ ln -s /usr/lib/python2.7/dist-packages/gobject/ gobject
    $ ln -s /usr/lib/python2.7/dist-packages/gtk-2.0* gtk-2.0
    $ ln -s /usr/lib/python2.7/dist-packages/pygtk.pth pygtk.pth
    $ ln -s /usr/lib/python2.7/dist-packages/cairo cairo
    $ ln -s /usr/lib/python2.7/dist-packages/webkit/ webkit
    $ ln -s /usr/lib/python2.7/dist-packages/webkit.pth webkit.pth
    $ cd -
    $ . venv/bin/activate
    (venv)$ ./w3af_gui
    (venv)$ . /tmp/w3af_dependency_install.sh


Each time you want to run ``w3af`` in a new console you'll have to activate the
virtualenv:

.. code-block:: console

    $ cd w3af
    $ . venv/bin/activate
    (venv)$ ./w3af_console
