#!/bin/bash

pip install mock pylint httpretty psutil logilab-astng SOAPpy PIL SimpleCV==1.3

bzr branch lp:xpresser
cd xpresser/
python setup.py install
cd ..

