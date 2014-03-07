Automation using scripts
========================

While developing w3af, we realized the need of fast and easy way to execute the same steps over and over, so the script functionality was born. w3af can run a script file using the ``-s`` argument. Script files are text files with one ``w3af_console`` command on each line. An example script file would look like this:

.. code-block:: none

    plugins
    output text_file
    output config text_file
    set output_file output-w3af.txt
    set verbose True
    back

.. note::

   Scripts are great for running periodic scans against your site using cron!

.. note::

   Example script files can be found inside the ``scripts/`` directory.

VIM syntax file
---------------

A `VIM syntax file <http://www.vim.org/scripts/script.php?script_id=4567>`_ for ``w3af`` script editing is provided and maintained by the project development team.

