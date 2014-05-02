Updating to the latest version
==============================

Manually updating
-----------------

Manually updating to the latest ``w3af`` version is trivial:

.. code-block:: bash

    cd w3af/
    git pull

.. note::

   After an update, ``w3af`` might require new dependencies.

Auto-update feature
-------------------

The framework includes an auto-update feature. This feature allows you to run our latest Git version without worrying about executing the ``git pull`` command. You can configure your local w3af instance to update itself for you once a day, weekly or monthly.

The auto-update feature is enabled by default and its configuration can be changed using the ``~/.w3af/startup.conf`` file. The file is generated after the first run.

.. code-block:: bash

    [STARTUP_CONFIG]
    last-update = 2013-01-24
    frequency = D
    auto-update = true

The feature can be completely disabled by setting the ``auto-update`` section to ``false``; and the update frequency has ``D``, ``W`` and ``M`` (daily, weekly and monthly) as valid values.

It is also possible to force the update to take place, or not, by simply giving the ``w3af_console`` or ``w3af_gui`` scripts the desired option:
``--force-update`` or ``--no-update``.

Branches
--------

.. note::

   This section is only interesting for advanced users.

We use ``git flow`` to manage our development process, this means that you'll find the latest stable code at ``master``, a development version at ``develop`` and experiments and unstable code in ``feature`` branches. I encourage advanced users to experiment with the code at ``develop`` and ``feature`` branches and report bugs, it helps us advance our development and get real testers while we don't disturb other users that require stable releases.

.. code-block:: bash

    git clone git@github.com:andresriancho/w3af.git
    cd w3af/
    git checkout develop
    git branch
    
