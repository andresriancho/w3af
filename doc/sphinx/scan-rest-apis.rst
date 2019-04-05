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

Providing custom parameter values for API endpoints
---------------------------------------------------

The ``crawl.open_api`` plugin tries to guess valid values for parameters of API endpoints.
The plugin takes into account types of parameters and other info from the API specification,
and then tries its best to find acceptable parameter values.
But these values may highly depend on the context.
For example, if an API endpoint takes an numeric user ID as a parameter,
then most probably the plugin will use a number for this parameter,
although most likely it's going to be an invalid user ID.
As a result, the chance that the endpoint will reject such requests is quite high
because there is no user with such ID. If the plugin knew a valid user ID for testing,
it might increase chances to catch a vulnerability
which might exist after that check for a valid user ID.

If users have some knowledge about correct values which may be used for testing,
they can tell the plugin about them via ``parameter_values_file`` configuration parameter.
The parameter specifies a path to a YAML config which contains values
which should be used by the plugin to fill out parameters in HTTP requests.

Here is an example of such a YAML config:

::

    - path: /users/{user-id}
      parameters:
      - name: user-id
        values:
        - 1234567
      - name: X-First-Name
        values:
        - John
        - Bill
      - path: /users
        parameters:
        - name: user-id
          values:
          - 1234567
        - name: X-Birth-Date
          values:
          - 2000-01-02

The configuration above tells the ``crawl.open_api`` plugin the following:

 * For the ``/users/{user-id}`` endpoint, use ``1234567`` number for ``user-id`` parameter,
   and ``John`` and ``Bill`` strings for ``X-First-Name`` parameter.
 * For the ``/users`` endpoint, use ``1234567`` number for ``user-id`` parameter,
   and ``2000-01-02`` date for ``X-Birth-Date`` parameter.

If a user provides multiple values for parameters, then the plugin tries to enumerate
all possible combinations of parameters. With the configuration above,
the plugin is going to generate at least three HTTP requests
which are going to look like the following:

::

    GET /users/1234567
    X-First-Name: John
    ...

    GET /users/1234567
    X-First-Name: Bill
    ...

    POST /users?user-id=1234567
    X-Birth-Date: 200-01-02
    ...

In this example, we made several assumptions about the API specification for the endpoints:

 * Both ``X-First-Name`` and ``X-Birth-Data`` are headers
 * ``user-id`` is a parameter in query string for the ``/users`` endpoint.
 * The ``/users/{user-id}`` endpoint accepts GET requests.
 * The ``/users`` endpoint accepts POST requests.

Note that the plugin doesn't currently take parameter types into account.
