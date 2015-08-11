Introduction
============

Before running ``w3af`` users need to know the basics about how the application
works behind the scenes. This will enable users to be more efficient in the
process of identifying and exploiting vulnerabilities.

Main plugin types
-----------------

The framework has three main plugins types: ``crawl``, ``audit`` and ``attack``.

Crawl plugins
*************

They have only one responsibility, finding new URLs, forms, and other injection
points. A classic example of a discovery plugin is the web spider. This plugin
takes a URL as input and returns one or more injection points.

When a user enables more than one plugin of this type, they are run in a loop:
If ``plugin A`` finds a new URL in the first run, the ``w3af`` core will send
that URL to ``plugin B``. If ``plugin B`` then finds a new URL, it will be sent
to ``plugin A``. This process will go on until all plugins have run and no more
information about the application can be found.

Audit plugins
*************

Take the injection points found by crawl plugins and send specially crafted data
to all in order to identify vulnerabilities. A classic example of an audit plugin
is one that searches for SQL injection vulnerabilities by sending ``a'b"c`` to
all injection points.

Attack plugins
**************

Their objective is to exploit vulnerabilities found by audit plugins. They
usually return a shell on the remote server, or a dump of remote tables in the
case of SQL injection exploits.

Other plugins
-------------

Infrastructure
**************

Identify information about the target system such as installed WAF (web
application firewalls), operating system and HTTP daemon.

Grep
****

Analyze HTTP requests and responses which are sent by other plugins and identify
vulnerabilities. For example, a grep plugin will find a comment in the HTML body
that has the word “password” and generate a vulnerability.

Output
******

The way the framework and plugins communicate with the user. Output plugins save
the data to a text, xml or html file. Debugging information is also sent to the
output plugins and can be saved for analysis.

Messages sent to the output manager are sent to all enabled plugins, so if you
have enabled ``text_file`` and ``xml_file`` output plugins, both will log any
vulnerabilities found by an audit plugin.

.. note::

   Ideas:
    * Send vulnerabilities to an internal issue tracker using its REST API
    * Parse ``w3af``'s XML output and use it as input for other tools


Mangle
******

Allow modification of requests and responses based on regular expressions, think
"sed (stream editor) for the web".

Bruteforce
**********

Bruteforce logins found during the ``crawl`` phase.

Evasion
*******

Evade simple intrusion detection rules by modifying the HTTP traffic generated
by other plugins.


Scan configuration
------------------

After configuring the ``crawl`` and ``audit`` plugins, and setting the target
URL the user starts the scan and waits for the vulnerabilities to appear in the
user interface.

Any vulnerabilities which are found during the scan phase are stored in a
knowledge base; which is used as the input for the ``attack`` plugins. Once the
scan finishes the user will be able to execute the ``attack`` plugins on the
identified vulnerabilities.

Configuration recommendations
-----------------------------

At this point it should be obvious but:

.. warning::

   Scan time will strongly depend on the number of ``crawl`` and ``audit``
   plugins you enable.

In most cases we recommend running ``w3af`` with the following configuration:
 
 * ``crawl``: ``web_spider``
 * ``audit``: ``Enable all``
 * ``grep``: ``Enable all``

