The ``/traffic/`` resource
==========================

Once a ``w3af`` scan starts the plugins send HTTP requests which get stored in
an internal database. HTTP requests and responses associated with a vulnerability
can be accessed using the REST API at ``/scans/<scan-id>/traffic/<traffic-id>``.

The most common flow is to access the vulnerability details at
``/scans/<scan-id>/kb/<vulnerability-id>`` and use the ``traffic_hrefs`` object
attribute to perform requests to the traffic resources.

Encoding
--------

The HTTP request and response is encoded using base64 in order to allow the REST
API to send special characters (null bytes, etc.) without encoding problems.
