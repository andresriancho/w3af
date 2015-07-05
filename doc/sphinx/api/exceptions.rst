The ``/exceptions/`` resource
=============================

In most cases ``w3af`` will complete the scan process without raising any
exceptions, but when it does all the information related to the raised
exceptions is stored and accessible using the ``/scans/<scan-id>/exceptions/``
endpoint.

Reporting vulnerabilities
-------------------------

If you're writing a client that will consume ``w3af``'s REST API please consider
implementing an automated bug report feature that will read the exceptions at
the end of the scan and create an issue in our github repository.

The traceback and all the reported exception data is sanitized before leaving
the REST API, the data will not contain the target domain, user information or
any other information from the target web application or host where the scanner
is running.

Please contact us at our IRC channel if you've got any doubts about this.