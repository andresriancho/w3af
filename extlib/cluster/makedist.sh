#!/bin/bash

python setup.py sdist
python setup.py bdist
python setup.py bdist_rpm
python setup.py bdist_wininst


