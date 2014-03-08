Running w3af
------------

w3af has two user interfaces, the console user interface and the graphical user interface. This user guide will focus on the console user interface, where it's easier to explain the framework's features. To fire up the console UI execute:

.. code-block:: none

    $ ./w3af_console
    w3af>>>


From this prompt you will be able to configure framework and plugin settings, launch scans and ultimately exploit a vulnerability. At this point you can start typing commands. The first command you have to learn is ``help`` (please note that commands are case sensitive):


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

The main menu commands are explained in the help that is displayed above. The internals of every menu will be seen later in this document. As you already noticed, the ``help`` command can take a parameter, and if available, a detailed help for that command will be shown, e.g. ``help keys``.

Other interesting things to notice about the console UI is the ability for tabbed completion (type 'plu' and then TAB) and the command history (after typing some commands, navigate the history with the up and down arrows).

To enter a configuration menu, you just have to type it's name and hit enter, you will see how the prompt changes and you are now in that context:

.. code-block:: none

    w3af>>> http-settings
    w3af/config:http-settings>>>

All the configuration menus provide the following commands:

 * ``help``
 * ``view``
 * ``set``
 * ``back``

Here is a usage example of this commands in the ``http-settings`` menu:

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
    |---------------------------------------------------------------------------------------------------|
    | Setting                | Value    | Description                                                   |
    |---------------------------------------------------------------------------------------------------|
    | url_parameter          |          | Append the given URL parameter to every accessed URL.         |
    |                        |          | Example: http://www.foobar.com/index.jsp;<parameter>?id=2     |
    | timeout                | 15       | The timeout for connections to the HTTP server                |
    | headers_file           |          | Set the headers filename. This file has additional headers    |
    |                        |          | which are added to each request.                              |
    |---------------------------------------------------------------------------------------------------|
    ...
    |---------------------------------------------------------------------------------------------------|
    | basic_auth_user        |          | Set the basic authentication username for HTTP requests       |
    | basic_auth_passwd      |          | Set the basic authentication password for HTTP requests       |
    | basic_auth_domain      |          | Set the basic authentication domain for HTTP requests         |
    |---------------------------------------------------------------------------------------------------|
    w3af/config:http-settings>>> set timeout 5
    w3af/config:http-settings>>> save
    w3af/config:http-settings>>> back
    w3af>>>

To summarize, the ``view`` command is used to list all configurable parameters, with their values and a description. The set command is used to change a value. Finally we can execute ``back``, “.” or press CTRL+C to return to the previous menu. A detailed help for every configuration parameter can be obtained using ``help parameter`` as shown in this example:

.. code-block:: none

    w3af/config:http-settings>>> help timeout
    Help for parameter timeout:
    ===========================
    Set low timeouts for LAN use and high timeouts for slow Internet connections.

    w3af/config:http-settings>>>


The ``http-settings`` and the ``misc-settings`` configuration menus are used to set system wide parameters that are used by the framework. All the parameters have defaults and in most cases you can leave them as they are. w3af was designed in a way that allows beginners to run it without having to learn a lot of its internals.

It is also flexible enough to be tuned by experts that know what they want and need to change internal configuration parameters to fulfill their tasks.

Running w3af with GTK user interface
------------------------------------

The framework has also a graphical user interface that you can start by executing:

.. code-block:: none

    $ ./w3af_gui

The graphical user interface allows you to perform all the actions that the framework offers and features a much easier and faster way to start a scan and analyze the results.

.. note::

   The GUI has different third party dependencies and might require you to install extra OS and python packages.

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

All plugins except the ``attack`` plugins can be configured within this menu. Lets list all the plugins of the ``audit`` type:

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

To enable the ``xss`` and ``sqli`` plugins, and then verify that the command was understood by the framework, we issue this set of commands:


**w3af/plugins>>>**
audit xss, sqli

**w3af/plugins>>>**
audit

|------------------------------------------------------------|

| Plugin name
| Status
| Conf | Description
|

|------------------------------------------------------------|

...

| sqli
| Enabled |
| Find SQL injection
|

|
|
|
| bugs.
|

...

| xss
| Enabled | Yes
| Find cross site
|

|
|
|
| scripting
|

|
|
|
| vulnerabilities.
|

| xst
|
|
| Verify Cross Site
|

|
|
|
| Tracing
|

|
|
|
| vulnerabilities.
|

|------------------------------------------------------------|

**w3af/plugins>>>**


Or if the user is interested in knowing exactly what a plugin does, he can also run the “
desc”
command like this:


**w3af>>>**
plugins

**w3af/plugins>>>**
audit desc fileUpload


This plugin will try to expoit insecure file upload forms.


One configurable parameter exists:

- extensions


The extensions parameter is a comma separated list of extensions that this plugin will try to upload. Many web applications
verify the extension of the file being uploaded, if special extensions are required, they can be added here.


Some web applications check the contents of the files being uploaded to see if they are really what their extension
is telling. To bypass this check, this plugin uses file templates located at "plugins/audit/fileUpload/", this templates

are valid files for each extension that have a section ( the comment field in a gif file for example ) that can be replaced

by scripting code ( PHP, ASP, etc ).


After uploading the file, this plugin will try to find it on common directories like "upload" and "files" on every know directory. If the file is found, a vulnerability exists.


**w3af/plugins>>>**


Now we know what this plugin does, but let's check their internals:


**w3af/plugins>>>**
audit config xss

**w3af/plugins/audit/config:xss>>> **
view

|------------------------------------------------------------|

| Setting
| Value | Description
|

|------------------------------------------------------------|

| numberOfChecks
| 3
| Set the amount of checks to
|

|
|
| perform for each fuzzable
|

|
|
| parameter. Valid numbers: 1 to
|

|
|
| 13
|

| checkStored
| True
| Search persistent XSS
|

|------------------------------------------------------------|


**w3af/plugin/xss>>>**
** **
set checkStored False

**w3af/plugin/xss>>>**
back

**w3af/plugins>>>**
audit config sqli

**w3af/plugins/audit/config:sqli>>> **
view

|------------------------------------------------------------|

| Setting
| Value
| Description
|

|------------------------------------------------------------|

|------------------------------------------------------------|

**w3af/plugins/audit/config:sqli>>> **

**w3af/plugins/audit/config:sqli>>> **
back

**w3af/plugins>>>**


The configuration menus for the plugins also have the set command for changing the parameters values, and the view command for listing existing values. On the previous example we disabled persistent cross site scripting checks in the xss plugin, and listed the options of the sqli plugin (it actually has no configurable parameters).


Starting a scan
---------------


After configuring all desired plugins the user has to set the target URL and finally start the scan. The target selection is done this way:


**w3af>>>**
target

**w3af/config:target>>> **
set target http://localhost/

**w3af/config:target>>>**
back

**w3af>>>**


Finally, you execute “start” in order to run all the configured plugins.


**w3af>>>**
start


At any time during the scan, you may hit “enter” in order to get a live status of the w3af core. Status lines look like this:

Status: Running discovery.webSpider on http://localhost/w3af/ | Method: GET.



A complete session
~~~~~~~~~~~~~~~~~~


An example of an entir
e
w3af session
appears below.
Attention should be paid to the inline comments as they provide additional details
.


**$**
./w3af

**w3af>>>**
plugins

**w3af/plugins>>>**
output console,textFile

**w3af/plugins>>>**
output config textFile

**w3af/plugins/output/config:textFile>>>**
set fileName output-w3af.txt

**w3af/plugins/output/config:textFile>>>**
set verbose True

**w3af/plugins/output/config:textFile>>>**
back

**w3af/plugins>>>**
output config console

**w3af/plugins/output/config:console>>>**
set verbose False

**w3af/plugins/output/config:console>>>**
back


All this previous commands have enabled two output plugins, console and textFile and configured them as needed.


**w3af/plugins>>>**
discovery allowedMethods,webSpider

**w3af/plugins>>>**
back


In this case, we will be running only discovery plugins. The enabled plugins are allowedMethods and webSpider .


**w3af>>>**
target

**w3af/target>>>**
set target http://localhost/w3af/

**w3af/target>>>**
back

**w3af>>>**
start

New URL found by discovery: http://localhost/w3af/responseSplitting/responseSplitting.php

New URL found by discovery: http://localhost/w3af/blindSqli/blindSqli-str.php

New URL found by discovery: http://localhost/w3af/webSpider/2.html

...

...

The URL: http://localhost/beef/hook/ has DAV methods enabled:

- OPTIONS

- GET

- HEAD

- POST

- TRACE

- PROPFIND

- PROPPATCH

- COPY

- MOVE

- LOCK

- UNLOCK

- DELETE ( is possibly enabled too, not tested for safety )

New URL found by discovery: http://localhost/w3af/globalRedirect/wargame/

New URL found by discovery: http://localhost/w3af/globalRedirect/w3af-site.tgz


After the discovery phase is finished a summary is presented to the user:


The list of found URLs is:

- http://localhost/w3af/globalRedirect/w3af.testsite.tgz

- http://localhost/beef/hook/beefmagic.js.php

- http://localhost/w3af/globalRedirect/2.php

*   http://localhost/w3af/webSpider/11.html

    ...




A section of the summary is the points of injection that will be used in the audit phase:


Found 78 URLs and 102 different points of injection.

The list of Fuzzable requests is:

- http://localhost/w3af/ | Method: GET

- http://localhost/w3af/responseSplitting/responseSplitting.php | Method: GET | Parameters: (header)

*   http://localhost/w3af/sqli/dataReceptor.php | Method: POST | Parameters: (user,firstname)



Finally the user exits the application, returning to the shell.

**w3af>>>**
exit

w3af, better than the regular script kiddie.

**$**








