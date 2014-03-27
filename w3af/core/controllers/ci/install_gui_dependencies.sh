#!/bin/bash -x

# There are a couple of GUI dependencies which need to be installed 
# using "apt-get". Asked the circle guys to install them and they
# recommended me to run this command to make sure the virtualenv
# can access these packages

if [ ! -d venv/lib/python2.7/dist-packages ]; then
    mkdir venv/lib/python2.7/dist-packages
    ln -s /usr/lib/python2.7/dist-packages/glib/ venv/lib/python2.7/dist-packages/
    ln -s /usr/lib/python2.7/dist-packages/gobject/ venv/lib/python2.7/dist-packages/
    ln -s /usr/lib/python2.7/dist-packages/gtk-2.0* venv/lib/python2.7/dist-packages/
    ln -s /usr/lib/python2.7/dist-packages/pygtk.pth venv/lib/python2.7/dist-packages/
    ln -s /usr/lib/python2.7/dist-packages/cairo venv/lib/python2.7/dist-packages/
    ln -s /usr/lib/python2.7/dist-packages/pygtk.py venv/lib/python2.7/dist-packages/
    ln -s /usr/lib/python2.7/dist-packages/gi venv/lib/python2.7/dist-packages/
    ln -s /usr/lib/python2.7/dist-packages/gtksourceview2.so venv/lib/python2.7/dist-packages/
fi

# Install the GUI dependencies
python -c 'from w3af.core.ui.gui.dependency_check.dependency_check import dependency_check;dependency_check()'

if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi