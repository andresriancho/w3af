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
from os.path import join
from uuid import uuid4
from tempfile import tempdir

import w3af.core.controllers.output_manager as om

from w3af.core.ui.api.db.master import SCANS, ScanInfo
from w3af.core.ui.api.utils.log_handler import RESTAPIOutput
from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.data.parsers.doc.url import URL


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
    scan_profile_file = join(tempdir, '%s.pw3af' % uuid4())
    file(scan_profile_file, 'w').write(scan_profile)

    return scan_profile_file, tempdir


def start_scan_helper(target_urls, scan_profile, scan_info_setup):
    """
    Create a new instance of w3afCore, save it to SCANS and run core.start()

    :param scan_profile: The contents of a profile configuration
    :param scan_info_setup: Event to set when the scan started
    :return: The instance of w3afCore.
    """
    scan_info = ScanInfo()
    SCANS[get_new_scan_id()] = scan_info
    scan_info.w3af_core = w3af_core = w3afCore()
    scan_info.target_urls = target_urls
    scan_info.output = RESTAPIOutput()

    scan_info_setup.set()

    scan_profile_file_name, profile_path = create_temp_profile(scan_profile)

    # Clear all current output plugins
    om.manager.set_output_plugins([])

    try:
        # Load the profile with the core and plugin config
        w3af_core.profiles.use_profile(scan_profile_file_name,
                                       workdir=profile_path)

        # Override the target that's set in the profile
        target_options = w3af_core.target.get_options()
        target_option = target_options['target']

        target_option.set_value([URL(u) for u in target_urls])
        w3af_core.target.set_options(target_options)

        w3af_core.plugins.init_plugins()

        # Add the REST API output plugin
        om.manager.set_output_plugin_inst(scan_info.output)

        # Start the scan!
        w3af_core.verify_environment()
        w3af_core.start()
    except Exception, e:
        scan_info.exception = e
        w3af_core.stop()
    finally:
        scan_info.finished = True

