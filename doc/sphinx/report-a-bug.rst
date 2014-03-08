Bug reporting
=============

The framework is under continuous development and we might introduce bugs and regressions while trying to implement new features. We use continuous integration and heavy unit and integration testing to avoid most of these but some simply reach to our users (doh!)

Good bug reporting practices
----------------------------

If you're using the latest version of the framework and find a bug, please `report it <https://github.com/andresriancho/w3af/issues/new>`_ including the following information:

 * Detailed steps to reproduce it
 * Python traceback
 * Operating system
 * Output of the ``./w3af_console --version`` command
 * Log file with verbose set to ``True`` (see below)

Basic debugging
---------------

When you want to know what the framework is doing the best way is to enable the ``text_file`` output plugin, making sure that the ``verbose`` configuration setting set to ``true``. This will generate a very detailed output file which can be used to gain an insight on ``w3af``'s internals.

.. code-block:: none

    plugins
    output text_file
    output config text_file
    set verbose True
    back

False negatives
---------------

If ``w3af`` is failing to identify a vulnerability which you manually verified please make sure that:

 * The ``audit`` plugin that identifies that vulnerability is enabled
 * Using basic debugging, make sure that ``w3af`` finds the URL and parameter associated with the vulnerability. If you don't see that in the log, make sure the ``crawl.web_spider`` plugin is enabled.

False negatives should be `reported just like bugs <https://github.com/andresriancho/w3af/issues/new>`_ , including all the same information.

False positives
---------------

Nobody likes false positives, you go from the adrenaline of "The site is vulnerable to SQL injection!" to "Nope, false positive" in less than a minute. Not good for your heart.

Please report the false positivese `like bugs <https://github.com/andresriancho/w3af/issues/new>`_ , in our repository. Include as much information as possible, remember that we'll have to verify the false positive, write a unittest and then fix it.