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

    $ ./w3af_api -p "<SHA512-hashed password for basic authentication>"
     * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

Or it can also be run inside a docker container:

.. code-block:: none

    $ cd extras/docker/scripts/
    $ ./w3af_api_docker -c /path/to/config_file.yaml
     * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)

A password is required for HTTP basic authentication, and can be specified on
the command line with the "-p" flag, or in a configuration file with the
"password:" directive.

To simplify passing options to the API when run with Docker, the helper script
asks users to create and specify a configuration file.

Authentication
--------------

Linux or Mac users can generate a SHA512 hash from a plaintext password by
running:

.. code-block:: none
    $ echo -n "secret" | sha512sum
    bd2b1aaf7ef4f09be9f52ce2d8d599674d81aa9d6a4421696dc4d93dd0619d682ce56b4d64a9ef097761ced99e0f67265b5f76085e5b0ee7ca4696b2ad6fe2b2  -

If the above hash was specified using the "password" option, users would be able 
to authenticate using HTTP basic auth with the default username 'admin' and 
password 'secret'.

For example, using the 'curl' command:

.. code-block:: none
    $ curl -u admin:secret http://127.0.0.1:5000
    {
      "docs": "http://docs.w3af.org/en/latest/api/index.html" 
    }

Config file format
------------------

Using a configuration file is completely optional unless you're starting the
API using the provided Docker scripts. It's simply a convenient place to put
configuration options that could otherwise be specified on the command line.

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

In the above example, all values except 'password' are the defaults and could
have been omitted from the configuration file without changing the way the API 
runs.

REST API Source code
--------------------

The `REST API <https://github.com/andresriancho/w3af/tree/master/w3af/core/ui/api/>`_
is implemented in Flask and is pretty well documented for your reading pleasure.

REST API clients
----------------

Wrote a REST API client? Let us know and get it linked here!

 * `Official Python REST API client <https://github.com/andresriancho/w3af-api-client>`_ which is also available at `pypi <https://pypi.python.org/pypi/w3af-api-client>`_


Contents
--------

.. toctree::
   :maxdepth: 2

   scans
   kb
   version
   traffic
