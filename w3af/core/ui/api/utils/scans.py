"""
scans.py

Copyright 2015 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""
import os

from uuid import uuid4
from tempfile import tempdir

from w3af.core.ui.api.db.master import SCANS
import w3af.core.controllers.output_manager as om


def get_scan_info_from_id(scan_id):
    return SCANS.get(scan_id, None)


def get_new_scan_id():
    return len(SCANS.keys())


def create_temp_profile(scan_profile):
    """
    Writes the scan_profile to a file

    :param scan_profile: The contents of a profile configuration
    :return: The scan profile file name and the directory where it was created
    """
    scan_profile_file = os.path.join(tempdir, '%s.pw3af' % uuid4())
    file(scan_profile_file, 'w').write(scan_profile)

    return scan_profile_file, tempdir


def remove_temp_profile(scan_profile_file_name):
    """
    Remove temp profile after using
    :param scan_profile_file_name: path to the temp profile
    :return: None
    """
    try:
        os.remove(scan_profile_file_name)
    except OSError:
        pass


def start_scan_helper(scan_info):
    """
    Start scan from scan_info

    :param scan_info: ScanInfo object contains initialized w3afCore
    """
    w3af_core = scan_info.w3af_core
    try:
        # Init plugins!
        w3af_core.plugins.init_plugins()

        # Clear all current output plugins
        # Add the REST API output plugin
        om.manager.set_output_plugins([])
        om.manager.set_output_plugin_inst(scan_info.output)

        # Start the scan!
        w3af_core.verify_environment()
        w3af_core.start()
    except Exception, e:
        scan_info.exception = e
        try:
            w3af_core.stop()
        except AttributeError:
            # Reduce some exceptions found during interpreter shutdown
            pass

    finally:
        scan_info.finished = True

        try:
            os.unlink(scan_info.profile_path)
        except (AttributeError, IOError) as _:
            # Reduce some exceptions found during interpreter shutdown
            pass

