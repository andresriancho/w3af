The ``/sessions/`` resource
===========================

:doc:`scans` can be used to quickly and easily start a scan from an
existing ``w3af`` profile, and to monitor the progress or results of any scan 
run using the REST API.

For more complex requests, a scan can be configured by using the ``/sessions/``
endpoint. This allows a user of the API to specify which plugins should be
enabled, and to modify individual plugin or core w3af settings as needed before
the scan is run.

Once created, scans built using the ``/sessions/`` resource can be viewed from 
:doc:`scans` in the same way as any other API scan.

A high-level overview of the process is as follows:

 * Request a new session using ``POST`` to ``/sessions/``. This will return a numeric session ID (eg '0').
 * Configure plugins, targets and/or other core settings by sending a ``PATCH`` request to the the relevant endpoint under ``/sessions/<id>/`` (see below).
 * Start the scan by sending an empty ``POST`` request to ``/sessions/<id>/start``
 * View the scan status and results using :doc:`scans` and :doc:`kb`.

.. note::
   Configured scans can also be removed in the same way as any other scan, by
   sending a ``DELETE`` request to the ``/scans/<id>`` endpoint.
.. note::
   Multiple sessions may exist and be configured simultaneously. However at 
   present the REST API only allows one scan to actually be running at any given 
   time.

Endpoints
---------

The following endpoints and HTTP methods are available:

 * ``POST`` ``/sessions/`` : creates a session and returns a numeric ID ('0' in the examples below).
 * ``GET`` ``/sessions/0/plugins/`` : returns the available plugin categories.
 * ``GET`` ``/sessions/0/plugins/<plugin_type>/`` : returns all available plugins of ``<plugin_type>`` (eg all 'crawl' plugins').
 * ``GET`` ``/sessions/0/plugins/<plugin_type>/<plugin_name>/`` : returns help text, current state and available options for the selected plugin.
 * ``PATCH`` ``/sessions/0/plugins/<plugin_type>/<plugin_name>/`` : accepts requests to modify plugin settings.
 * ``GET`` ``/sessions/0/core/<target|http|misc>/`` : returns available framework settings and their current values.
 * ``PATCH`` ``/sessions/0/core/<target|http|misc>/`` : accepts requests to modify core framework settings.
 * ``POST`` ``/sessions/0/start/`` : starts a scan from the configured session.

As with the rest of the API all responses are in JSON format and any request
data is expected to be in valid JSON format as well. It is recommended to set
the ``Content-Type: application/json`` header when sending request data.

Configuring a session
---------------------

The following worked example will configure and start a scan as outlined in the
overview above using the ``curl`` utility for Linux/Mac systems.

.. note::
   This will be a very minimal scan for the purposes of illustration. In
   practice, API users will almost certainly want to configure several plugins, 
   including at least one ``audit`` plugin.

First, we must create a session:

.. code-block:: none

    $ curl -X POST 'http://127.0.0.1:5000/sessions/'
    {
      "href": "/sessions/0", 
      "id": 0, 
      "message": "Success"
    }

This returns the session ID and endpoint URL for further configuration. A ``GET`` 
request to :doc:`scans` shows that the created `session` can also be seen as a 
`scan` with the same numeric ID:

.. code-block:: none

    $ curl 'http://127.0.0.1:5000/scans'
    {
      "items": [
        {
          "errors": false, 
          "href": "/scans/0", 
          "id": 0, 
          "status": "Stopped", 
          "target_urls": null
        }
      ]
    }

However, this scan won't run yet as it has no target and no plugins enabled.
We can see the available plugins using ``/plugins/`` and the endpoints beneath
it:

.. code-block:: none

    $ curl 'http://127.0.0.1:5000/sessions/0/plugins/'
    {
      "entries": [
        "audit", 
        "auth", 
        "bruteforce", 
        "crawl", 
        "evasion", 
        "grep", 
        "infrastructure", 
        "mangle", 
        "output"
      ]
    }

    $ curl 'http://127.0.0.1:5000/sessions/0/plugins/crawl/'
    {
      "description": "Crawl plugins use different techniques to identify new URLs, forms, and any other resource that might be of use during the audit and bruteforce phases.", 
      "entries": [
        "archive_dot_org", 
        "bing_spider", 
        [...]
        "web_spider", 
        "wordnet", 
        "wordpress_enumerate_users", 
        "wordpress_fingerprint", 
        "wordpress_fullpathdisclosure", 
        "wsdl_finder"
      ]
    }

There are more crawl plugins than this available, but the list has been 
abbreviated here to save space. 

A ``GET`` request shows the available options for the ``web-spider`` plugin:

.. code-block:: none

    $ curl 'http://127.0.0.1:5000/sessions/0/plugins/crawl/web_spider'
    {
      "configuration": {
        "follow_regex": {
          "default": ".*", 
          "description": "When crawling only follow which that match this regular expression. Please note that ignore_regex has precedence over follow_regex.", 
          "type": "regex", 
          "value": ".*"
        }, 
        "ignore_regex": {
          "default": "", 
          "description": "When crawling, DO NOT follow links that match this regular expression. Please note that ignore_regex has precedence over follow_regex.", 
          "type": "regex", 
          "value": ""
        }, 
        "only_forward": {
          "default": "False", 
          "description": "When crawling only follow links to paths inside the one given as target.", 
          "type": "boolean", 
          "value": "False"
        }
      }, 
      "description": "This plugin is a classic web spider, it will request a URL and extract all links and forms from the response. Three configurable parameter exist: - only_forward - ignore_regex - follow_regex ignore_regex and follow_regex are commonly used to configure the web_spider to spider all URLs except the \"logout\" or some other more exciting link like \"Reboot Appliance\" that would make the w3af run finish without the expected result. By default ignore_regex is an empty string (nothing is ignored) and follow_regex is '.*' (everything is followed). Both regular expressions are normal regular expressions that are compiled with Python's re module. The regular expressions are applied to the URLs that are found using the match function.", 
      "enabled": false
    }

Since we haven't changed any settings in our example, all values shown are the
defaults. ``enabled`` is ``false``, meaning that the plugin is not set to run as
part of the final scan.

Sending a ``PATCH`` request allows us to enable the plugin, and/or change its
settings from the default. Let's do both in a single request:

.. code-block:: none

    $ curl -H 'Content-Type: application/json' \
           -X PATCH 'http://127.0.0.1:5000/sessions/0/plugins/crawl/web_spider' \
           --data '{"enabled":"true","ignore_regex":".*xml"}'
    {
      "message": "success", 
      "modified": {
        "enabled": "true", 
        "ignore_regex": ".*xml"
      }
    } 


A ``GET`` request to ``/sessions/0/plugins/crawl/web_spider/`` shows that the
plugin is now ``enabled`` and that the value for ``ignore_regex`` has been
updated:

.. code-block:: none

    $ curl 'http://127.0.0.1:5000/sessions/0/plugins/crawl/web_spider/'
    {
      "configuration": {
        [...]
        "ignore_regex": {
          "default": "", 
          "description": "When crawling, DO NOT follow links that match this regular expression. Please note that ignore_regex has precedence over follow_regex.", 
          "type": "regex", 
          "value": ".*xml"
        }, 
        [...]
      }, 
      "description": [...],
      "enabled": true
    }

In order to start a scan, at least one plugin must be enabled and a target must
be configured:

.. code-block:: none

    $ curl 'http://127.0.0.1:5000/sessions/0/core/target/'
    {
      "target settings": {
        "target": {
          "default": "[]", 
          "description": "A comma separated list of URLs", 
          "type": "url_list", 
          "value": "[]"
        }, 
        "target_framework": {
          "default": "unknown", 
          "description": "Target programming framework (unknown/php/asp/asp.net/java/jsp/cfm/ruby/perl)", 
          "type": "combo", 
          "value": "unknown"
        }, 
        "target_os": {
          "default": "unknown", 
          "description": "Target operating system (unknown/unix/windows)", 
          "type": "combo", 
          "value": "unknown"
        }
      }

    $ curl -H 'Content-Type: application/json' \
     -X PATCH 'http://127.0.0.1:5000/sessions/0/core/target/' \
     --data '{"target":["http://localhost:8000"]}'
    {
      "message": "success", 
      "modified": {
        "target": [
          "http://localhost:8000"
        ]
      }
    }

    $ curl 'http://127.0.0.1:5000/sessions/0/start' -X POST
    {
      "href": "/scans/0", 
      "id": 0, 
      "message": "Success"
    }

The scan is now running, and :doc:`scans` can be used to see its progress. When
it is finished, the results will be available via :doc:`kb` and :doc:`traffic`.
