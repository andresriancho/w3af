The ``/urls/`` resource
=======================

Once a ``w3af`` scan starts the ``crawl`` plugins find new URLs which get stored
in the knowledge base, this information is important for the user to understand
which parts of the application were scanned and can be accessed using the REST
API endpoint at ``/scans/<scan-id>/urls/``.


The ``/fuzzable-requests/`` resource
====================================

Advanced users will find the ``/urls/`` information insufficient since it lacks
the parameters (query string, post-data, json) and headers which were identified
by ``w3af``. The ``/scans/<scan-id>/fuzzable-requests/`` endpoint returns a list
with all the raw HTTP requests that the scanner will use during the ``audit``
phase.

Encoding
--------

The fuzzable requests is encoded using base64 in order to allow the REST
API to send special characters (null bytes, etc.) without encoding problems.
