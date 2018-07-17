Authentication
==============
These types of authentication schemes are supported by w3af:

 * HTTP Basic authentication
 * NTLM authentication
 * Form authentication
 * Setting an HTTP cookie

If the user provides credentials ``w3af`` will make sure that the scan is run
using an active user session.

HTTP Basic and NTLM authentication are two types of HTTP level authentication
usually provided by the web server, while the form and cookie authentication
methods are provided by the application itself. It’s up to the user to identify
which authentication method is required to keep a session with the application,
but usually a quick inspection of the HTTP traffic will define what’s required.

Basic and NTLM authentication
-----------------------------
To configure basic or NTLM credentials open the HTTP settings menu. The
configuration set in this section will affect all plugins and other core libraries.

.. code-block:: none

    w3af>>> http-settings
    w3af/config:http-settings>>> view
    |--------------------------------------------------------------------------------------|
    | Setting                | Description                                                 |
    |--------------------------------------------------------------------------------------|
    ...
    |--------------------------------------------------------------------------------------|
    | ntlm_auth_url          | Set the NTLM authentication domain for HTTP requests        |
    | ntlm_auth_user         | Set the NTLM authentication username for HTTP requests      |
    | ntlm_auth_passwd       | Set the NTLM authentication password for HTTP requests      |
    | ntlm_auth_domain       | Set the NTLM authentication domain (the windows domain name)|
    |                        | requests. Please note that only NTLM v1 is supported.       |
    |--------------------------------------------------------------------------------------|
    ...
    |--------------------------------------------------------------------------------------|
    | basic_auth_user        | Set the basic authentication username for HTTP requests     |
    | basic_auth_passwd      | Set the basic authentication password for HTTP requests     |
    | basic_auth_domain      | Set the basic authentication domain for HTTP requests       |
    |--------------------------------------------------------------------------------------|
    w3af/config:http-settings>>>

Please note the two different configuration sections for basic HTTP authentication
and NTLM authentication. Enter your preferred settings and then ``save``. The scanner
is now ready to start an authenticated scan, the next step would be to enable
specific plugins and start the scan.

.. note::

    NTML and basic authentication usually require usernames with the ``\`` character,
    which needs to be entered as `\\\\` in the w3af-console. For example to use
    `domain\\user` as the user use ``set basic_auth_user domain\\user``.


Form authentication
-------------------
Form authentication has changed significantly in the latest w3af versions.
Starting with version 1.6 the form authentication is configured using ``auth``
plugins. There are two authentication plugins available in the framework:

 * detailed
 * generic

Authentication plugins are a special type of plugin which is responsible to keep
a session alive during the whole scan. These plugins are called before starting
the scan (in order to get a fresh session) and once every 5 seconds while the
scan is running (to verify if the current session is still alive and create a
new one if needed).

This tutorial will explain how to configure the ``generic`` authentication plugin
which has the following options:

 * ``username``: Web application’s username
 * ``password``: Web application’s password
 * ``username_field``: The name of the username form input that can be found in the login HTML source.
 * ``password_field``: The name of the password form input that can be found in the login HTML source.
 * ``auth_url``: The URL where the username and password are POST’ed to.
 * ``check_url``: The URL that will be used to check if the session is still active, usually this is set to the web application user’s settings page.
 * ``check_string``: A string that if found in the check_url’s HTTP response body proves that the session is still active, usually this is set to a string that can only be found in the user’s settings page, for example his last name.

Once all these settings have been configured, it is recommended to start a test
scan only with ``crawl.web_spider`` and ``auth.generic`` in order to verify that
all the post-authentication forms and links are identified. Also, keep an eye on
w3af’s log since the authentication plugins will create log entries if there is
any issue with the authentication process. Log entries like:

    ``Login success for admin/password``
    ``User "admin" is currently logged into the application``

Are what you would expect to see if the configuration was successful and messages
like:

    ``Can't login into web application as admin/password``

Show that either the plugin configuration is incorrect, or the application
requires more parameters to be sent to the auth_url which in some cases is solved
by using the detailed plugin.

.. warning::
    Configure the ``crawl.web_spider`` plugin to ignore the logout link. This is
    important since we want to keep the session alive for the duration of the
    scan.

.. note::

    Creating new authentication plugins is easy! Custom authentication types can
    be added by cloning the detailed auth plugin.

Setting HTTP Cookie
-------------------
For the cases in which the form authentication doesn’t work, which might be
related with login forms containing anti-CSRF tokens or two factor authentication,
``w3af`` provides users with a method to set one or more HTTP cookies to use during
the scan.

You can capture those cookies in any way you like: directly from the browser,
using a web proxy, wireshark, etc.

Create a `Netscape format cookie jar file <http://www.cookiecentral.com/faq/#3.5>`_
using a text editor, replacing the example values:

.. code-block:: none

    # Netscape HTTP Cookie File
    .netscape.com   TRUE    /   FALSE   946684799   NETSCAPE_ID 100103

Once the file is created set the ``cookie_jar_file`` setting in the ``http-settings``
menu to point to it.

.. warning::
    Make sure the file you've created follows the specification, Python's cookie
    parser is really strict and won't load cookies if any errors are found.

    The most common errors are to omit the dot at the beginning of the domain name
    (see .netscape.com) and to use spaces instead of tabs as a field separator
    (the example above uses tabs but the HTML renderer might replace it with spaces).

.. warning::
    Configure the ``crawl.web_spider`` plugin to ignore the logout link. This is
    important since we want to keep the session alive for the duration of the
    scan.

Setting HTTP headers
--------------------
Some Web applications use custom HTTP headers for authentication, this is also
supported by the w3af framework.

This method will set an HTTP request header which will be added to each HTTP
request that is sent by the framework, note that no verification of the session’s
state is made when using this method, if the session is invalidated the scan will
continue using the invalid session (header value).

In order to use this method you’ll first have to:

 * Create a text file using your favorite text editor with the following contents:
   ``Cookie: <insert-cookie-here>``, without the quotes and inserting the desired
   session cookie.

 * Then, in w3af’s ``http-settings`` configuration menu set the ``headers_file``
   configuration parameter to point to the recently created file.

 * ``save``

The w3af scanner is now configured to use the HTTP session cookie for all HTTP
requests.
