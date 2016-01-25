REST API Introduction
=====================

This documentation section is a user guide for w3af's REST API service, its goal
is to provide developers the knowledge to consume w3af as a service using any
development language.

We recommend you read through the `w3af users guide <http://docs.w3af.org/>`_
before diving into this REST API-specific section.

Starting the REST API service
-----------------------------

The REST API can be started by running:

.. code-block:: none

    $ ./w3af_api
     * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

Or it can also be run inside a docker container:

.. code-block:: none

    $ cd extras/docker/scripts/
    $ ./w3af_api_docker
     * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

Authentication
--------------

It is possible to require HTTP basic authentication for all REST API requests by
specifying a SHA512-hashed password on the command line (with ``-p <SHA512_HASH>``)
or in a configuration file using the ``password:`` directive (see the section
below for more information about configuration files).

Linux or Mac users can generate a SHA512 hash from a plaintext password by
running:

.. code-block:: none

    $ echo -n "secret" | sha512sum
    bd2b1aaf7ef4f09be9f52ce2d8d599674d81aa9d6a4421696dc4d93dd0619d682ce56b4d64a9ef097761ced99e0f67265b5f76085e5b0ee7ca4696b2ad6fe2b2  -

    $ ./w3af_api -p "bd2b1aaf7ef4f09be9f52ce2d8d599674d81aa9d6a4421696dc4d93dd0619d682ce56b4d64a9ef097761ced99e0f67265b5f76085e5b0ee7ca4696b2ad6fe2b2"
     * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

In the above example, users are only able to connect using HTTP basic
authentication with the default username ``admin`` and the password ``secret``.

For example, using the ``curl`` command:

.. code-block:: none

    $ curl -u admin:secret http://127.0.0.1:5000
    {
      "docs": "http://docs.w3af.org/en/latest/api/index.html" 
    }

Please note that even with basic authentication, traffic passing to and from the 
REST API is not encrypted, meaning that authentication and vulnerability
information could still be sniffed by an attacker with "man-in-the-middle"
capabilities.

When running the REST API on a publicly available IP address we recommend taking
additional precautions including running it behind an SSL proxy server (such as 
Pound, nginx, or Apache with mod_proxy enabled).

Config file format
------------------

Using a configuration file is optional and is simply a convenient place to store
settings that could otherwise be specified using command line arguments.

The configuration file is in standard YAML format and accepts any of the options
found on the command line. A sample configuration file would look like this:

.. code-block:: none

    # This is a comment
    host: '127.0.0.1'
    port: 5000
    verbose: False
    username: 'admin'
    # The SHA512-hashed password is 'secret'. We don't recommend using this.
    password: 'bd2b1aaf7ef4f09be9f52ce2d8d599674d81aa9d6a4421696dc4d93dd0619d682ce56b4d64a9ef097761ced99e0f67265b5f76085e5b0ee7ca4696b2ad6fe2b2'

In the above example, all values except ``password`` are the defaults and could
have been omitted from the configuration file without changing the way the API 
runs.

Serve using TLS/SSL
-------------------

``w3af``'s REST API is served using Flask, which can be used to deliver content
over TLS/SSL. By default ``w3af`` will generate a self signed certificate and
bind to port 5000 using the ``https`` protocol.

To disable ``https`` users can set the ``--no-ssl`` command line argument.

Advanced users who want to use their own SSL certificates can:

 * Start ``w3af`` in HTTP mode and use a proxy such as ``nginx`` to handle
   the SSL traffic and forward unencrypted traffic to the REST API.

 * Copy the user generated SSL certificate and key to ``/.w3af/ssl/w3af.crt``
   and ``/.w3af/ssl/w3af.key`` and start ``./w3af_api`` without ``--no-ssl``.

.. note::

    Using ``nginx`` to serve ``w3af``'s API will give the user more configuration
    options and security than running SSL in ``w3af_api``.

REST API Source code
--------------------

The `REST API <https://github.com/andresriancho/w3af/tree/master/w3af/core/ui/api/>`_
is implemented in Flask and is pretty well documented for your reading pleasure.

REST API clients
----------------

Wrote a REST API client? Let us know and get it linked here!

 * `Official Python REST API client <https://github.com/andresriancho/w3af-api-client>`_
   which is also available at `pypi <https://pypi.python.org/pypi/w3af-api-client>`_


API endpoints
-------------

.. toctree::
   :maxdepth: 2

   scans
   kb
   version
   traffic
   urls
   exceptions
