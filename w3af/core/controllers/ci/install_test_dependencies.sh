#!/bin/bash -x

#
# Install all libs required to run our tests (which are available at pypi)
#
pip install pylint==0.28.0 mock httpretty psutil logilab-astng SOAPpy PIL SimpleCV==1.3 termcolor==1.1.0

#
# Install xpresser
#
if [ ! -d "xpresser" ]; then
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
#       * python-opencv
#       * python-numpy
#       * python-scipy
# For the xpresser tests to work well, also I need to link to the
# system library from my virtualenv:
#
# Dependency tree: xpresser => simplecv => scipy => numpy
#                                       => python-opencv
#
if [ ! -L venv/lib/python2.7/dist-packages/pyatspi ]; then
    ln -s /usr/lib/python2.7/dist-packages/pyatspi/ venv/lib/python2.7/dist-packages/
    ln -s /usr/lib/python2.7/dist-packages/dbus/ venv/lib/python2.7/dist-packages/
    ln -s /usr/lib/python2.7/dist-packages/_dbus_bindings.so venv/lib/python2.7/dist-packages/
    ln -s /usr/lib/python2.7/dist-packages/pygame/ venv/lib/python2.7/dist-packages/
    ln -s /usr/lib/python2.7/dist-packages/numpy/ venv/lib/python2.7/dist-packages/
    ln -s /usr/lib/python2.7/dist-packages/scipy/ venv/lib/python2.7/dist-packages/
    ln -s /usr/lib/pyshared/python2.7/cv2.so venv/lib/python2.7/dist-packages/
fi
