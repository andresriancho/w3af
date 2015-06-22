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
