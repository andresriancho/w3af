#!/bin/bash -x

#
# Install all libs required to run our tests (which are available at pypi)
#
pip install pylint==0.28.0 mock==1.0.1 httpretty==0.7.0 psutil==1.2.1
pip install logilab-astng==0.24.3 SOAPpy==0.12.5 Pillow==1.7.8 SimpleCV==1.3
pip install termcolor==1.1.0 yanc==0.2.4 futures==2.1.5 fabric==1.8.0
pip install xunitparser==1.2.0

# Install requirements for coveralls
pip install coverage==3.6 nose-cov==1.6 coveralls==0.2

pip install --upgrade -e 'git+https://github.com/andresriancho/nose.git#egg=nose'

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
