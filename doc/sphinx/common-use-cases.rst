Common use cases
================
Due to the multiple configuration settings the framework has it's sometimes difficult
to find how to perform a specific task, this page explains how to perform some common
use cases using w3af.

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
