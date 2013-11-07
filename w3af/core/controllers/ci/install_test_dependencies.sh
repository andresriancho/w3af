#!/bin/bash -x

#
# Install all libs required to run our tests (which are available at pypi)
#
pip install pylint mock httpretty psutil logilab-astng SOAPpy PIL SimpleCV==1.3

#
# Install xpresser
#
if [ ! -d xpresser ]; then
    bzr branch lp:xpresser
    cd xpresser/
    python setup.py install
    cd ..
fi

#
# Required the guys from circleci to add these to my build:
#       * gir1.2-notify-0.7
#       * python-pyatspi2
#       * dbus-python
#       * python-pygame
# For the xpresser tests to work well, also I need to link to the
# system library from my virtualenv:
#
if [ ! -L venv/lib/python2.7/dist-packages/pyatspi ]; then
    ln -s /usr/lib/python2.7/dist-packages/pyatspi/ venv/lib/python2.7/dist-packages/
    ln -s /usr/lib/python2.7/dist-packages/dbus/ venv/lib/python2.7/dist-packages/
    ln -s /usr/lib/python2.7/dist-packages/_dbus_bindings.so venv/lib/python2.7/dist-packages/
    ln -s /usr/lib/python2.7/dist-packages/pygame/ venv/lib/python2.7/dist-packages/
fi

#
# Dependency tree: xpresser => simplecv => scipy
#
pip install scipy==0.13.0