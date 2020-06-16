Common use cases
================
Due to the multiple configuration settings the framework has it's sometimes difficult
to find how to perform a specific task, this page explains how to perform some common
use cases using w3af.

The JavaScript crawler
----------------------
`w3af` implements JavaScript crawling in the `crawl.web_spider` plugin. The JS crawler
is enabled by default and can be disabled (not recommended if you want to achieve high
test coverage) using the plugin's configuration.

The JS crawler uses either Google Chrome or Chromium to load the target pages and
interact with them.

.. warning::

   Google Chrome is recommended over Chromium. Performance tests indicate that Chromium
   is a bit slower.

The JS crawler is fully automated and does not require any configuration,
just enable `crawl.web_spider`!

Scanning only one directory
---------------------------
When auditing a site it's common to be interested in scanning only the URLs inside a
specific directory. In order to achieve this task follow these steps:

 * Set the target URL to ``http://domain/directory/``
 * Enable all ``audit`` plugins
 * Enable the ``crawl.web_spider`` plugin
 * In ``crawl.web_spider`` set the ``only_forward`` flag to ``True``

Using this configuration the crawler will only yield URLs which are inside ``/directory``.
Then audit plugins will only scan the URLs inside that directory.

Saving URLs and using them as input for other scans
---------------------------------------------------
Crawling can be an expensive process, which in some cases requires manual
intervention (spider man plugin). In order to save all the URLs found during a
scan it's possible to use the ``output.export_requests`` plugin which will write
the URLs to a user configured file.

Loading the saved data is achieved using the ``import_results`` plugin, which
reads all the information and feeds it into w3af's core.
