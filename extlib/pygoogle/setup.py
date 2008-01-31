#!/usr/bin/env python
from distutils.core import setup
import os

setup (name = "pygoogle",
    version = "0.5",
    description= "Simple interface to Google",
    long_description = "This module lets you search the Google search engine programmatically.  See http://www.google.com/apis/ for details." ,
    author = 'Brian Landers (origianlly by Mark Pilgrim and contributors)',
    author_email = 'brian@bluecoat93.org',
    packages = [''],
    package_dir = {'':os.curdir},
    extra_path = 'pygoogle',
    )
