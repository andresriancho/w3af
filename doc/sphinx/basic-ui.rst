Running w3af
============

``w3af`` has two user interfaces, the console user interface and the graphical
user interface. This user guide will focus on the console user interface where
it's easier to explain the framework's features. To fire up the console UI
execute:

.. code-block:: none

    $ ./w3af_console
    w3af>>>


From this prompt you will be able to configure framework and plugin settings,
launch scans and ultimately exploit a vulnerability. At this point you can start
typing commands. The first command you have to learn is ``help`` (please note
that commands are case sensitive):


.. code-block:: none

    w3af>>> help
    |----------------------------------------------------------------|
    | start         | Start the scan.                                |
    | plugins       | Enable and configure plugins.                  |
    | exploit       | Exploit the vulnerability.                     |
    | profiles      | List and use scan profiles.                    |
    | cleanup       | Cleanup before starting a new scan.            |
    |----------------------------------------------------------------|
    | help          | Display help. Issuing: help [command] , prints |
    |               | more specific help about "command"             |
    | version       | Show w3af version information.                 |
    | keys          | Display key shortcuts.                         |
    |----------------------------------------------------------------|
    | http-settings | Configure the HTTP settings of the framework.  |
    | misc-settings | Configure w3af misc settings.                  |
    | target        | Configure the target URL.                      |
    |----------------------------------------------------------------|
    | back          | Go to the previous menu.                       |
    | exit          | Exit w3af.                                     |
    |----------------------------------------------------------------|
    | kb            | Browse the vulnerabilities stored in the       |
    |               | Knowledge Base                                 |
    |----------------------------------------------------------------|
    w3af>>>
    w3af>>> help target
    Configure the target URL.
    w3af>>>

The main menu commands are explained in the help that is displayed above. The
internals of every menu will be seen later in this document. As you already
noticed, the ``help`` command can take a parameter, and if available, a detailed
help for that command will be shown, e.g. ``help keys``.

Other interesting things to notice about the console UI is the ability for
tabbed completion (type 'plu' and then TAB) and the command history (after
typing some commands, navigate the history with the up and down arrows).

To enter a configuration menu, you just have to type it's name and hit enter,
you will see how the prompt changes and you are now in that context:

.. code-block:: none

    w3af>>> http-settings
    w3af/config:http-settings>>>

All the configuration menus provide the following commands:

 * ``help``
 * ``view``
 * ``set``
 * ``back``

Here is a usage example of these commands in the ``http-settings`` menu:

.. code-block:: none

    w3af/config:http-settings>>> help
    |-----------------------------------------------------------------|
    | view  | List the available options and their values.            |
    | set   | Set a parameter value.                                  |
    | save  | Save the configured settings.                           |
    |-----------------------------------------------------------------|
    | back  | Go to the previous menu.                                |
    | exit  | Exit w3af.                                              |
    |-----------------------------------------------------------------|
    w3af/config:http-settings>>> view
    |-----------------------------------------------------------------------------------------------|
    | Setting                | Value    | Description                                               |
    |-----------------------------------------------------------------------------------------------|
    | url_parameter          |          | Append the given URL parameter to every accessed URL.     |
    |                        |          | Example: http://www.foobar.com/index.jsp;<parameter>?id=2 |
    | timeout                | 15       | The timeout for connections to the HTTP server            |
    | headers_file           |          | Set the headers filename. This file has additional headers|
    |                        |          | which are added to each request.                          |
    |-----------------------------------------------------------------------------------------------|
    ...
    |-----------------------------------------------------------------------------------------------|
    | basic_auth_user        |          | Set the basic authentication username for HTTP requests   |
    | basic_auth_passwd      |          | Set the basic authentication password for HTTP requests   |
    | basic_auth_domain      |          | Set the basic authentication domain for HTTP requests     |
    |-----------------------------------------------------------------------------------------------|
    w3af/config:http-settings>>> set timeout 5
    w3af/config:http-settings>>> save
    w3af/config:http-settings>>> back
    w3af>>>

To summarize, the ``view`` command is used to list all configurable parameters,
with their values and a description. The ``set`` command is used to change a
value. Finally we can execute ``back`` or press CTRL+C to return to the previous
menu. A detailed help for every configuration parameter can be obtained using
``help parameter`` as shown in this example:

.. code-block:: none

    w3af/config:http-settings>>> help timeout
    Help for parameter timeout:
    ===========================
    Set low timeouts for LAN use and high timeouts for slow Internet connections.

    w3af/config:http-settings>>>


The ``http-settings`` and the ``misc-settings`` configuration menus are used to
set system wide parameters that are used by the framework. All the parameters
have defaults and in most cases you can leave them as they are. ``w3af`` was
designed in a way that allows beginners to run it without having to learn a lot
of its internals.

It is also flexible enough to be tuned by experts that know what they want and
need to change internal configuration parameters to fulfill their tasks.

Running w3af with GTK user interface
------------------------------------

The framework has also a graphical user interface that you can start by executing:

.. code-block:: none

    $ ./w3af_gui

The graphical user interface allows you to perform all the actions that the
framework offers and features a much easier and faster way to start a scan and
analyze the results.

.. note::

   The GUI has different third party dependencies and might require you to
   install extra OS and python packages.

Plugin configuration
--------------------

The plugins are configured using the “plugins” configuration menu.

.. code-block:: none

    w3af>>> plugins
    w3af/plugins>>> help
    |-----------------------------------------------------------------------------|
    | list             | List available plugins.                                  |
    |-----------------------------------------------------------------------------|
    | back             | Go to the previous menu.                                 |
    | exit             | Exit w3af.                                               |
    |-----------------------------------------------------------------------------|
    | output           | View, configure and enable output plugins                |
    | audit            | View, configure and enable audit plugins                 |
    | crawl            | View, configure and enable crawl plugins                 |
    | bruteforce       | View, configure and enable bruteforce plugins            |
    | grep             | View, configure and enable grep plugins                  |
    | evasion          | View, configure and enable evasion plugins               |
    | infrastructure   | View, configure and enable infrastructure plugins        |
    | auth             | View, configure and enable auth plugins                  |
    | mangle           | View, configure and enable mangle plugins                |
    |-----------------------------------------------------------------------------|
    w3af/plugins>>> 

All plugins except the ``attack`` plugins can be configured within this menu.
Lets list all the plugins of the ``audit`` type:

.. code-block:: none

    w3af>>> plugins
    w3af/plugins>>> list audit
    |-----------------------------------------------------------------------------|
    | Plugin name        | Status | Conf | Description                            |
    |-----------------------------------------------------------------------------|
    | blind_sqli         |        | Yes  | Identify blind SQL injection           |
    |                    |        |      | vulnerabilities.                       |
    | buffer_overflow    |        |      | Find buffer overflow vulnerabilities.  |
    ...

To enable the ``xss`` and ``sqli`` plugins, and then verify that the command was
understood by the framework, we issue this set of commands:

.. code-block:: none

    w3af/plugins>>> audit xss, sqli
    w3af/plugins>>> audit
    |----------------------------------------------------------------------------|
    | Plugin name        | Status  | Conf | Description                          |
    |----------------------------------------------------------------------------|
    | sqli               | Enabled |      | Find SQL injection bugs.             |
    | ssi                |         |      | Find server side inclusion           |
    |                    |         |      | vulnerabilities.                     |
    | ssl_certificate    |         | Yes  | Check the SSL certificate validity   |
    |                    |         |      | (if https is being used).            |
    | un_ssl             |         |      | Find out if secure content can also  |
    |                    |         |      | be fetched using http.               |
    | xpath              |         |      | Find XPATH injection                 |
    |                    |         |      | vulnerabilities.                     |
    | xss                | Enabled | Yes  | Identify cross site scripting        |
    |                    |         |      | vulnerabilities.                     |
    | xst                |         |      | Find Cross Site Tracing              |
    |                    |         |      | vulnerabilities.                     |
    |----------------------------------------------------------------------------|
    w3af/plugins>>>


Or if the user is interested in knowing exactly what a plugin does, he can also
run the ``desc`` command like this:

.. code-block:: none

    w3af/plugins>>> audit desc xss

    This plugin finds Cross Site Scripting (XSS) vulnerabilities.

    One configurable parameters exists:
        - persistent_xss

    To find XSS bugs the plugin will send a set of javascript strings to
    every parameter, and search for that input in the response.

    The "persistent_xss" parameter makes the plugin store all data
    sent to the web application and at the end, request all URLs again
    searching for those specially crafted strings.

    w3af/plugins>>> 

Now we know what this plugin does, but let's check its internals:

.. code-block:: none

    w3af/plugins>>> audit config xss
    w3af/plugins/audit/config:xss>>> view
    |-----------------------------------------------------------------------------|
    | Setting        | Value | Description                                        |
    |-----------------------------------------------------------------------------|
    | persistent_xss | True  | Identify persistent cross site scripting           |
    |                |       | vulnerabilities                                    |
    |-----------------------------------------------------------------------------|
    w3af/plugins/audit/config:xss>>> set persistent_xss False
    w3af/plugins/audit/config:xss>>> back
    The configuration has been saved.
    w3af/plugins>>> 

The configuration menus for the plugins also have the ``set`` command for
changing the parameters values, and the ``view`` command for listing existing
values. On the previous example we disabled persistent cross site scripting
checks in the xss plugin.

Saving the configuration
------------------------

Once the plugin and framework configuration is set, it is possible to save this
information to a profile:

.. code-block:: none

    w3af>>> profiles
    w3af/profiles>>> save_as tutorial
    Profile saved.

Profiles are saved as files in ``~/.w3af/profiles/``. The saved configuration
can be loaded in order to run a new scan:

.. code-block:: none

    w3af>>> profiles
    w3af/profiles>>> use fast_scan
    The plugins configured by the scan profile have been enabled, and their options configured.
    Please set the target URL(s) and start the scan.
    w3af/profiles>>>

Sharing a profile with another user might be problematic, since they include
full paths to the files referenced by plugin configurations which would require
users to share the profile, referenced files, and manually edit the profile to
match the current environment. To solve this issue the ``self-contained`` flag
was added:

.. code-block:: none

    w3af>>> profiles
    w3af/profiles>>> save_as tutorial self-contained
    Profile saved.

A ``self-contained`` profile bundles all the referenced files inside the profile
and can be easily shared with other users.

Starting the scan
-----------------

After configuring all desired plugins the user has to set the target URL and
finally start the scan. The target selection is done this way:

.. code-block:: none

    w3af>>> target
    w3af/config:target>>> set target http://localhost/
    w3af/config:target>>> back
    w3af>>>

Finally, run ``start`` in order to run all the configured plugins.

.. code-block:: none

    w3af>>> start

At any time during the scan, you can hit ``<enter>`` in order to get a live
status of the w3af core. Status lines look like this:

.. code-block:: none

    Status: Running discovery.web_spider on http://localhost/w3af/ | Method: GET.
