Debugging
=========

Basic debugging
---------------

When you want to know what the framework is doing the best way is to enable the ``text_file`` output plugin, making sure that the ``verbose`` configuration setting set to ``true``. This will generate a very detailed output file which can be used to gain an insight on ``w3af``'s internals.

.. code-block:: none

    plugins
    output text_file
    output config text_file
    set verbose True
    back