The ``/kb/`` resource
=====================

Once a ``w3af`` scan has started the knowledge base is populated with the
vulnerabilities which are identified by the plugins. This information can be
accessed using the REST API using these resources:

 * ``/scans/<scan-id>/kb/`` returns all the identified vulnerabilities in a list
 * ``/scans/<scan-id>/kb/<vulnerability-id>`` returns detailed information about a vulnerability


List
----

Get a list of all known vulnerabilities:

.. code-block:: none

    $ curl http://127.0.0.1:5000/scans/0/kb/
    {
      "items": [
        {
          "href": "/scans/0/kb/0",
          "id": 0,
          "name": "SQL injection",
          "url": "http://127.0.0.1:8000/audit/sql_injection/where_integer_qs.py"
        },
        {
          "href": "/scans/0/kb/1",
          "id": 1,
          "name": "SQL injection",
          "url": "http://127.0.0.1:8000/audit/sql_injection/where_string_single_qs.py"
        },
        {
          "href": "/scans/0/kb/2",
          "id": 2,
          "name": "SQL injection",
          "url": "http://127.0.0.1:8000/audit/sql_injection/where_integer_form.py"
        },
        {
          "href": "/scans/0/kb/3",
          "id": 3,
          "name": "SQL injection",
          "url": "http://127.0.0.1:8000/audit/sql_injection/where_integer_form.py"
        }
      ]
    }


Knowledge base filters
----------------------

It is possible to filter the vulnerability list using two different query
string parameters, ``name`` and ``url``. If more than one filter is provided in
the HTTP request then they are combined using the ``AND`` boolean expression.


Details
-------

Get detailed information about a specific vulnerability:

.. code-block:: none

    $ curl http://127.0.0.1:5000/scans/0/kb/1
    {
      "attributes": {
        "db": "Unknown database",
        "error": "syntax error"
      },
      "cwe_ids": [
        "89"
      ],
      "cwe_urls": [
        "https://cwe.mitre.org/data/definitions/89.html"
      ],
      "desc": "SQL injection in a Unknown database was found at: \"http://127.0.0.1:8000/audit/sql_injection/where_string_single_qs.py\", using HTTP method GET. The sent data was: \"uname=a%27b%22c%27d%22\" The modified parameter was \"uname\".",
      "fix_effort": 50,
      "fix_guidance": "The only proven method to prevent against SQL injection attacks while still maintaining full application functionality is to use parameterized queries (also known as prepared statements). When utilising this method of querying the database, any value supplied by the client will be handled as a string value rather than part of the SQL query.\n\nAdditionally, when utilising parameterized queries, the database engine will automatically check to make sure the string being used matches that of the column. For example, the database engine will check that the user supplied input is an integer if the database column is configured to contain integers.",
      "highlight": [
        "syntax error"
      ],
      "href": "/scans/0/kb/1",
      "id": 1,
      "long_description": "Due to the requirement for dynamic content of today's web applications, many rely on a database backend to store data that will be called upon and processed by the web application (or other programs). Web applications retrieve data from the database by using Structured Query Language (SQL) queries.\n\nTo meet demands of many developers, database servers (such as MSSQL, MySQL, Oracle etc.) have additional built-in functionality that can allow extensive control of the database and interaction with the host operating system itself. An SQL injection occurs when a value originating from the client's request is used within a SQL query without prior sanitisation. This could allow cyber-criminals to execute arbitrary SQL code and steal data or use the additional functionality of the database server to take control of more server components.\n\nThe successful exploitation of a SQL injection can be devastating to an organisation and is one of the most commonly exploited web application vulnerabilities.\n\nThis injection was detected as the tool was able to cause the server to respond to the request with a database related error.",
      "name": "SQL injection",
      "owasp_top_10_references": [
        {
          "link": "https://www.owasp.org/index.php/Top_10_2013-A1",
          "owasp_version": "2013",
          "risk_id": 1
        }
      ],
      "plugin_name": "sqli",
      "references": [
        {
          "title": "SecuriTeam",
          "url": "http://www.securiteam.com/securityreviews/5DP0N1P76E.html"
        },
        {
          "title": "Wikipedia",
          "url": "http://en.wikipedia.org/wiki/SQL_injection"
        },
        {
          "title": "OWASP",
          "url": "https://www.owasp.org/index.php/SQL_Injection"
        },
        {
          "title": "WASC",
          "url": "http://projects.webappsec.org/w/page/13246963/SQL%20Injection"
        },
        {
          "title": "W3 Schools",
          "url": "http://www.w3schools.com/sql/sql_injection.asp"
        },
        {
          "title": "UnixWiz",
          "url": "http://unixwiz.net/techtips/sql-injection.html"
        }
      ],
      "response_ids": [
        45
      ],
      "traffic_hrefs": [
        "/scans/0/traffic/45"
      ],
      "severity": "High",
      "tags": [
        "web",
        "sql",
        "injection",
        "database",
        "error"
      ],
      "url": "http://127.0.0.1:8000/audit/sql_injection/where_string_single_qs.py",
      "var": "uname",
      "vulndb_id": 45,
      "wasc_ids": [],
      "wasc_urls": []
    }

