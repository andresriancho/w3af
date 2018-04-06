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

Ignoring specific forms
-----------------------

``w3af`` allows users to configure which forms to ignore using a feature called
form ID exclusions. This feature was created when users identified limitations in
the previous (more simplistic) exclusion model which only allowed forms to be
ignored using URL matching.

Exclusions are configured using a list of form IDs provided in the following format:

.. code-block:: json

    [{"action":"/products/.*",
      "inputs": ["comment"],
      "attributes": {"class": "comments-form"},
      "hosted_at_url": "/products/.*",
      "method": "get"}]

Where:

 * ``action`` is a regular expression matching the URL path of the form action,
 * ``inputs`` is a list containing the form inputs,
 * ``attributes`` is a map containing the ``<form>`` tag attributes,
 * ``hosted-at-url`` is a regular expression matching the URL path where the form was found,
 * ``method`` is the HTTP method using to submit the form.

So, for example, if a user wants to ignore all forms which are sent using the
HTTP POST method he would configure the following form ID:

.. code-block:: json

    [{"method": "post"}]

If the user decides to ignore all forms which are sent to a specific action and contain
the ``class`` attribute with value ``comments-form`` he would configure:

.. code-block:: json

    [{"action":"/products/comments",
      "attributes": {"class": "comments-form"}}]

More than one form ID can be specified in the list, for example the following will
exclude all forms with methods ``POST`` and ``PUT``:

.. code-block:: json

    [{"method": "post"}, {"method": "put"}]

Ignoring all forms is also possible using:

.. code-block:: json

    [{}]

This feature is configured using two variables in the ``misc-settings`` menu:

 * ``form_id_list``: A string containing the format explained above to match forms.
 * ``form_id_action``: The default action is to exclude the forms which are found
   by ``w3af`` and match at least one of the form IDs specified in ``form_id_list``,
   but the user can also specify ``include`` to only scan the forms which match at least
   one of the form IDs in the list.

To ease the configuration of this setting ``w3af`` will add a ``debug`` line to the
output (make sure to set verbose to true to see these lines in the output file plugin)
containing the form ID of each identified form.

.. note::

    This feature works well together with ``non_targets``.
    ``w3af`` will only send requests to the target if they match both filters.

Variants
--------

Crawling web applications is a challenging task: some web applications have
thousands of URLs, some of those with one or more HTML forms. Let's explore a
common e-commerce site which has one thousand products, each shown in a different
URL such as:

 * /products/title-product-A
 * /products/another-product-title
 * /review-comment?id=6631

When browsing to each of those URLs the HTML contains three forms, one to add the
product to the cart, another one to favorite the product and finally one to
ask a question regarding this product. The form action for each form is set to
the product page.

The main goal of an application security scan is to achieve full test coverage
(all the application code is tested) with the least amount of HTTP requests.

``w3af`` needs to be able to efficiently crawl sites like this, reducing the
number of HTTP requests to reach full test coverage. Some assumptions can be
made:

 * Submitting the form that will favorite one product will run the same server
 side code to favorite another product in the same e-commerce site.

 * Browsing ``/product/*`` pages will always run the same server side code and
 show the same three HTML forms.

 * Requesting ``/review-comment?id=*`` will always return a comment.

If we believe those to be true, then we can simply request a few samples instead of all.
The number of samples to collect can be configured with these ``misc`` settings are for:

 * ``path_max_variants``: Limit how many product pages will be crawled
 * ``params_max_variants``: Limit how many variants to sample for URLs with the same path and parameter names
 * ``max_equal_form_variants``: Limit how many forms with the same parameters but different URLs to sample

The default should suit most of the sites, but advanced users might want to modify
these settings when the scan is taking too much time or, multiple areas of the
application are not being scanned and the debug log shows many messages containing
the ``Ignoring ... simply a variant``.
