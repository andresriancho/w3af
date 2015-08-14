Advanced use cases
==================

Complex Web applications
------------------------

Some Web applications use browser-side technologies such as JavaScript, Flash
and Java applets, technologies that the browsers understand; and ``w3af``
is still unable to.

A plugin called ``spider_man`` was created to solve this issue, allowing users
to analyze complex Web applications. The plugin starts an HTTP proxy which is
used by the user to navigate the target site, during this process the plugin
will extract information from the requests and send them to the enabled
``audit`` plugins.

.. note::

    The ``spider_man`` plugin can be used when Javascript, Flash, Java applets
    or any other browser side technology is present. The only requirement is for
    the user to manually browse the site using ``spider_man`` as HTTP(s) proxy.

.. note::

    See :doc:`ca-config` for details about how to configure ``w3af``'s
    certificate authority (CA) in your browser.


A simple example will clarify things, let's suppose that ``w3af`` is auditing a
site and can't find any links on the main page. After a closer inspection of
the results by the user, it is clear that the main page has a Java applet menu
where all the other sections are linked from. The user runs ``w3af`` once again
and now activates the ``crawl.spider_man`` plugin, navigates the site manually
using the browser and the spiderman proxy. When the user has finished his
browsing, w3af will continue with all the hard auditing work.

This is a sample ``spider_man`` plugin run:

.. code-block:: none

    w3af>>> plugins 
    w3af/plugins>>> crawl spider_man
    w3af/plugins>>> audit sqli
    w3af/plugins>>> back
    w3af>>> target
    w3af/target>>> set target http://localhost/
    w3af/target>>> back
    w3af>>> start
    spider_man proxy is running on 127.0.0.1:44444 .
    Please configure your browser to use these proxy settings and navigate the target site.
    To exit spider_man plugin please navigate to http://127.7.7.7/spider_man?terminate .


Now the user configures his browser to use the ``127.0.0.1:44444`` address as
HTTP proxy and navigates the target site, when he finishes navigating the site
sections he wants to audit he navigates to ``http://127.7.7.7/spider_man?terminate``
which will stop the proxy and finish the plugin. The ``audit.sqli`` plugin will
run over the identified HTTP requests.

REST APIs
---------

``w3af`` can be used to identify and exploit vulnerabilities in REST APIs. The
two most common ways to consume a REST API are:

 * JavaScript which is delivered as part of a Web application
 * A program that runs outside the browser

It's important to notice that from ``w3af``'s point of view it's exactly the
same if the HTTP requests are generated from a browser or any other program,
thus it is possible to use ``spider_man`` proxy from any REST API client.

Just follow these steps to identify vulnerabilities in a REST API which is
consumed using a non-browser application:

 * Start ``spider_man`` using the steps outlined in the previous section
 * Configure the REST API client to send HTTP requests through ``127.0.0.1:44444`
 * Run the REST API client
 * Stop the ``spider_man`` proxy using ``curl -X GET http://127.7.7.7/spider_man?terminate --proxy http://127.0.0.1:44444``

.. note::

    Since REST APIs can not be crawled ``w3af`` will only audit the HTTP
    requests captured by the proxy. The manual step(s) where the user teaches
    ``w3af`` about all the API endpoints and parameters is key to the success
    of the security audit.