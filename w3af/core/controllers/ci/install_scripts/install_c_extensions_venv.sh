#!/usr/bin/env bash

mkdir -p /home/ubuntu/virtualenvs/venv-2.7.3/lib/python2.7/dist-packages/
cd /home/ubuntu/virtualenvs/venv-2.7.3/lib/python2.7/dist-packages/
ln -s /usr/lib/python2.7/dist-packages/glib/ glib
ln -s /usr/lib/python2.7/dist-packages/gobject/ gobject
ln -s /usr/lib/python2.7/dist-packages/gtk-2.0* gtk-2.0
ln -s /usr/lib/python2.7/dist-packages/pygtk.pth pygtk.pth
ln -s /usr/lib/python2.7/dist-packages/cairo cairo
ln -s /usr/lib/python2.7/dist-packages/webkit/ webkit
ln -s /usr/lib/python2.7/dist-packages/webkit.pth webkit.pth
