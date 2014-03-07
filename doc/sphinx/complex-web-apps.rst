Complex web applications
========================

Some Web applications use browser-side technologies like JavaScript, Macromedia Flash and Java applets, technologies that the browsers understand; and ``w3af`` is still unable to.

A plugin called ``spider_man`` was created to solve this issue, allowing users to analyze complex Web applications. The plugin script runs an HTTP proxy for the user to navigate the target site through it. During this process the plugin will extract information from the requests and send them to the enabled ``audit`` plugins.

.. note::

    The ``spider_man`` plugin can be used when Javascript, Flash, Java applets or any other browser side technology is present. The only requirement is for the user to browse through the whole site manually and the Web application to send HTTP requests.

Spiderman example
-----------------

A simple example will clarify things, let's suppose that ``w3af`` is auditing a site and can't find any links on the main page. After a closer interpretation of the results by the user, it is clear that the main page has a Java applet menu where all the other sections are linked
from. The user runs ``w3af`` once again and now activates the ``crawl.spider_man`` plugin, navigates the site manually using the browser and the spiderman proxy. When the user has finished his browsing, w3af will continue with all the hard auditing work.

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


Now the user configures the browser to use the ``127.0.0.1:44444`` address as his browser proxy and navigates the target site, when he finished navigating the site sections he wants to audit he navigates to ``http://127.7.7.7/spider_man?terminate`` stop the proxy and finish the plugin. The ``audit.sqli`` plugin will run over the identified URLs.
