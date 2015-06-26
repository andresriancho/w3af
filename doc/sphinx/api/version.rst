The ``/version`` resource
=========================

Query the w3af version using the REST API:

.. code-block:: none

    $ curl http://127.0.0.1:5000/version
    {
      "branch": "develop",
      "dirty": "Yes",
      "revision": "f1cae98161 - 24 Jun 2015 16:29",
      "version": "1.7.2"
    }
