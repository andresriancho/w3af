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

SSL Installation
----------------

The spider_man plugin works great on non-secure sites, however, to crawl a secure site, the spider_man plugin requires an additional SSL Certificate to be installed.  This tutorial will help with the steps to install the SSL Certificate in Firefox, Internet Explorer, Chrome, and Opera browsers.

Ideally use private browsing mode when recording the session. This should ensure that the browser starts with no stored cookies, and prevents certain changes from being saved. For example, Firefox does not allow certificate overrides to be saved permanently.

HTTPS recording and certificates
--------------------------------
HTTPS connections use certificates to authenticate the connection between the browser and the web server. When connecting via HTTPS, the server presents the certificate to the browser. To authenticate the certificate, the browser checks that the server certificate is signed by a Certificate Authority (CA) that is linked to one of its in-built root CAs. [Browsers also check that the certificate is for the correct host or domain, that it is valid and not expired.] If any of the browser checks fail, it will prompt the user who can then decided whether to allow the connection to proceed.

``w3af`` needs to use its own certificate to enable it to intercept the HTTPS connection from the browser. Effectively ``w3af`` has to pretend to be the target server.

The certificate was installed when ``w3af`` was installed and is located <enter location here>

``w3af`` uses a single certificate for all target servers. This certificate is not one of the certificates that browsers normally trust, and will not be for the correct host.

As a consequence the browser should display a dialogue asking if you want to accept the certificate or not. For example:
    1) The server's name "www.example.com" does not match the certificate's name "``w3af``". Somebody may be trying to eavesdrop on you.
    2) The certificate for "``w3af``" is signed by the unknown Certificate Authority "``w3af``". It is not possible to verify that this is a valid certificate.

Accept the certificate in order to allow the ``w3af`` Proxy to intercept the SSL traffic in order to record it. However, do not accept this certificate permanently; it should only be accepted temporarily. Browsers only prompt this dialogue for the certificate of the main url, not for the resources loaded in the page, such as images, css or javascript files hosted on a secured external CDN. If you have such resources (gmail has for example), you'll have to first browse manually to these other domains in order to accept ``w3af``'s certificate for them.

    If the browser has already registered a validated certificate for this domain, the browser will detect ``w3af`` as a security breach and will refuse to load the page. If so, you have to remove the trusted certificate from your browser's keystore.

If your browser currently uses a proxy (e.g. a company intranet may route all external requests via a proxy), then you need to tell ``w3af`` to use that proxy before crawling with spider_man.

Installing the ``w3af`` CA certificate for HTTPS recording
----------------------------------------------------------
Note that once the root CA certificate has been installed as a trusted CA, the browser will trust any certificates signed by it. Until such time as the certificate expires or the certificate is removed from the browser, it will not warn the user that the certificate is being relied upon. 

Installing the certificate in Firefox
-------------------------------------

Choose the following options:

    * Tools / Options
    * Advanced / Certificates
    * View Certificates
    * Authorities
    * Import ...
    * Browse to the <insert directory here> directory, and click on the file w3af-key.pem , press Open
    * Select "Trust this CA to identify web sites", and press OK
    * Close dialogs by pressing OK as necessary

Installing the certificate in Chrome or Internet Explorer
---------------------------------------------------------
Both Chrome and Internet Explorer use the same trust store for certificates.

    Browse to the <insert directory here> directory, and click on the file w3af-key.pem, and open it
    Go back to the "General" tab, and click on "Install Certificate ..." and follow the Wizard prompts

Installing the certificate in Opera
-----------------------------------
    Tools / Preferences / Advanced / Security
    Manage Certificates...
    Select "Intermediate" tab, click "Import..."
    Browse to the <insert directory here> directory, and click on the file w3af-key.pem, and open it
