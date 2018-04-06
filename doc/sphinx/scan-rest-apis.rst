Scan REST APIs
==============

``w3af`` can be used to identify and exploit vulnerabilities in REST APIs.

The scanner supports extracting endpoints and parameters from REST APIs
documented using the `Open API specification <https://swagger.io/docs/specification/about/>`_ ,
this means that ``w3af`` will be able to scan these APIs in a completely
automated way.

When the REST API is not documented using the Open API specification, the user
will have to use ``spider_man`` to feed the HTTP requests associated with the
REST API calls into the framework.

Scanning REST APIs with an Open API
-----------------------------------

The ``crawl.open_api`` plugin can be used to identify the location of the
Open API specification document (usually ``openapi.json`` in the API root directory)
and parse it.

After parsing the endpoints, headers and parameters the plugin sends this
information to ``w3af``'s core, where the audit plugin can be used to
identify vulnerabilities.

Using this plugin to scan REST APIs is easy, but here are some tips:

 * If you know the Open API specification document URL, include it in ``w3af``'s
   target URLs, this will make sure that the API is found and scanned.

 * If you have credentials, provide them in ``query_string_auth`` or ``header_auth``,
   this information will be added to all HTTP requests associated with the REST API.

Enabling this plugin even when you don't know if the REST API is documented
using the Open API specification is also a good idea, since the plugin will
find the document and create an informational finding to make sure it is
manually reviewed.

Feeding HTTP requests into w3af
-------------------------------

When the REST API is not documented using the Open API specification, the only
way for ``w3af`` to find all endpoints and parameters is for the user to manually
feed this information into the framework.

This process can be used for any REST API, just follow these steps to feed the
HTTP requests into ``w3af``:

 * Start ``spider_man`` using the steps outlined in ``Advanced use cases``
 * Configure the REST API client to send HTTP requests through ``127.0.0.1:44444``
 * Run the REST API client
 * Stop the ``spider_man`` proxy using ``curl -X GET http://127.7.7.7/spider_man?terminate --proxy http://127.0.0.1:44444``

.. note::

    Since these REST APIs can not be crawled ``w3af`` will only audit the HTTP
    requests captured by the proxy. The steps where the user teaches ``w3af``
    about all the API endpoints and parameters is key to the success
    of the security audit.
