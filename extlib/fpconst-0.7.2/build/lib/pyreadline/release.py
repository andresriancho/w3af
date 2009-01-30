# -*- coding: utf-8 -*-
"""Release data for the pyreadline project.

$Id: release.py 2514 2007-07-19 17:01:31Z jstenar $"""

#*****************************************************************************
#       Copyright (C) 2006  Jorgen Stenarson. <jorgen.stenarson@bostream.nu>
#
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#*****************************************************************************

# Name of the package for release purposes.  This is the name which labels
# the tarballs and RPMs made by distutils, so it's best to lowercase it.
name = 'pyreadline'

# For versions with substrings (like 0.6.16.svn), use an extra . to separate
# the new substring.  We have to avoid using either dashes or underscores,
# because bdist_rpm does not accept dashes (an RPM) convention, and
# bdist_deb does not accept underscores (a Debian convention).

branch = ''

#version = '1.5.svn'
version = '1.5'

revision = '$Revision: 2514 $'

description = "A python implmementation of GNU readline."

long_description = \
"""
The pyreadline package is a python implementation of GNU readline functionality
it is based on the ctypes based UNC readline package by Gary Bishop. 
It is not complete. It has been tested for use with windows 2000 and windows xp.

Features:
 *  NEW: keyboard text selection and copy/paste
 *  Shift-arrowkeys for text selection
 *  Control-c can be used for copy activate with allow_ctrl_c(True) is config file
 *  Double tapping ctrl-c will raise a KeyboardInterrupt, use ctrl_c_tap_time_interval(x)
    where x is your preferred tap time window, default 0.3 s.
 *  paste pastes first line of content on clipboard. 
 *  ipython_paste, pastes tab-separated data as list of lists or numpy array if all data is numeric
 *  paste_mulitline_code  pastes multi line code, removing any empty lines.
 *  Experimental support for ironpython. At this time Ironpython has to be patched for it to work.
 
 
 The latest development version is always available at the IPython subversion
 repository_.

.. _repository: http://ipython.scipy.org/svn/ipython/pyreadline/trunk#egg=pyreadline-dev
 """

license = 'BSD'

authors = {'Jorgen' : ('Jorgen Stenarson','jorgen.stenarson@bostream.nu'),
           'Gary':    ('Gary Bishop', ''),         
           'Jack':    ('Jack Trainor', ''),         
           }

url = 'http://ipython.scipy.org/moin/PyReadline/Intro'

download_url = ''

platforms = ['Windows XP/2000/NT','Windows 95/98/ME']

keywords = ['readline','pyreadline']

classifiers = ['Development Status :: 4 - Beta',
               'Environment :: Console',
               'Operating System :: Microsoft :: Windows',]
               
               
