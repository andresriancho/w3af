The ``/scans/`` resource
========================

Scanning a Web application using w3af's REST API requires the developer to
understand this basic workflow:

 * Start a new scan using ``POST`` to ``/scans/``
 * Get the scan status using ``GET`` to ``/scans/0``
 * Use :doc:`kb` to get information about the identified vulnerabilities
 * Clear all scan results before starting a new scan by sending a ``DELETE`` to ``/scans/0``

Optionally send these requests to control and monitor the scan:

 * Get a list of all currently running scans using a ``GET`` to ``/scans/``
 * Pause the scan using ``GET`` to ``/scans/0/pause``
 * Stop the scan using ``GET`` to ``/scans/0/stop``
 * Retrieve the scan log using ``GET`` to ``/scans/0/log``

.. warning::

   The current REST API implementation does not allow users to run more than
   one concurrent scan.

.. note::

   In the previous examples I've used ``/scans/0`` (note the hard-coded zero in
   the URL) as an example. When starting a new scan a new ID will be created.

Starting a scan
---------------

Performing a ``POST`` to the ``/scans/`` resource is one of the most complex
requests in our REST API. The call requires two specially crafted variables:

 * ``scan_profile`` which must contain the contents of a ``w3af`` scan profile (not the file name)
 * ``target_urls`` a list containing URLs to seed ``w3af``'s crawler

.. code-block:: python

    import requests
    import json

    data = {'scan_profile': file('/path/to/profile.pw3af').read(),
            'target_urls': ['http://127.0.0.1:8000/audit/sql_injection/']}

    response = requests.post('http://127.0.0.1:5000/scans/',
                             data=json.dumps(data),
                             headers={'content-type': 'application/json'})


.. note::

   Remember to send the ``Content-Type: application/json`` header