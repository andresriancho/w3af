# -*- Mode: Python; py-indent-offset: 4 -*-
# pygtk - Python bindings for the GTK+ widget set.
# Copyright (C) 1998-2002  James Henstridge
#
#   pygtk.py: pygtk version selection code.
#
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA

import fnmatch
import glob
import os
import os.path
import sys

__all__ = ['require']

_our_dir = os.path.dirname(os.path.abspath(os.path.normpath(__file__)))
_pygtk_2_0_dir = os.path.normpath('%s/gtk-2.0' % _our_dir)

_pygtk_dir_pat = 'gtk-[0-9].[0-9]'

_pygtk_required_version = None

def _get_available_versions():
    versions = {}
    for dir in sys.path:
        if not dir: 
  	    dir = os.getcwd()
            
        if not os.path.isdir(dir):
            continue
        
        # if the dir is a pygtk dir, skip it
        if fnmatch.fnmatchcase(os.path.basename(dir), _pygtk_dir_pat):
            continue  
        
        for filename in glob.glob(os.path.join(dir, _pygtk_dir_pat)):
            pathname = os.path.join(dir, filename)

            # skip non directories
            if not os.path.isdir(pathname):
                continue
            
            # skip empty directories
            if not os.listdir(pathname):
                continue
            
	    if not versions.has_key(filename[-3:]):
            	versions[filename[-3:]] = pathname
    return versions

def require20():
    if _pygtk_2_0_dir not in sys.path:
        sys.path.insert(0, _pygtk_2_0_dir)

def require(version):
    if version == '2.0':
        return require20()
    
    global _pygtk_required_version

    if _pygtk_required_version != None:
        assert _pygtk_required_version == version, \
               "a different version of gtk was already required"
        return

    assert not sys.modules.has_key('gtk'), \
           "pygtk.require() must be called before importing gtk"

    versions = _get_available_versions()
    assert versions.has_key(version), \
           "required version '%s' not found on system" % version

    # remove any pygtk dirs first ...
    for dir in sys.path:
        if fnmatch.fnmatchcase(os.path.basename(dir), _pygtk_dir_pat):
            sys.path.remove(dir)

    # prepend the pygtk path ...
    sys.path.insert(0, versions[version])
    
    _pygtk_required_version = version
