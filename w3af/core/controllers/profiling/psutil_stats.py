"""
psutil_stats.py

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
import json
import psutil

from .utils import get_filename_fmt, dump_data_every_thread, cancel_thread


PROFILING_OUTPUT_FMT = '/tmp/w3af-%s-%s.psutil'
DELAY_MINUTES = 2
SAVE_PSUTIL_PTR = []


def should_dump_psutil(wrapped):
    def inner(w3af_core):
        _should_profile = os.environ.get('W3AF_PSUTILS', '0')

        if _should_profile.isdigit() and int(_should_profile) == 1:
            return wrapped(w3af_core)

    return inner


@should_dump_psutil
def start_psutil_dump(w3af_core):
    """
    If the environment variable W3AF_PSUTILS is set to 1, then we start
    the thread that will dump the operating system data which can be retrieved
    using psutil module.

    :return: None
    """
    dump_data_every_thread(dump_psutil, DELAY_MINUTES, SAVE_PSUTIL_PTR)


def dump_psutil():
    """
    Dumps operating system information to file
    """
    output_file = PROFILING_OUTPUT_FMT % get_filename_fmt()

    process_info = {}
    for proc in psutil.process_iter():
        try:
            pinfo = proc.as_dict(attrs=['pid', 'name', 'parent', 'status',
                                        'io_counters', 'num_threads',
                                        'cpu_times', 'cpu_percent',
                                        'memory_info_ex', 'memory_percent',
                                        'exe', 'cmdline'])
        except psutil.NoSuchProcess:
            pass
        else:
            for info_name, info_data in pinfo.iteritems():
                if hasattr(info_data, '_asdict'):
                    pinfo[info_name] = dict(info_data._asdict())
                else:
                    pinfo[info_name] = info_data

            process_info[pinfo['pid']] = pinfo

    netinfo = psutil.net_io_counters(pernic=True)
    for key, value in netinfo.iteritems():
        netinfo[key] = value._asdict()

    # Merge all the data here
    psutil_data = {'CPU': psutil.cpu_times()._asdict(),
                   'Load average': os.getloadavg(),
                   'Virtual memory': psutil.virtual_memory()._asdict(),
                   'Swap memory': psutil.swap_memory()._asdict(),
                   'Network': netinfo,
                   'Processes': process_info}
    
    json.dump(psutil_data, file(output_file, 'w'), indent=4, sort_keys=True)


@should_dump_psutil
def stop_psutil_dump(w3af_core):
    """
    Save profiling information (if available)
    """
    cancel_thread(SAVE_PSUTIL_PTR)
    dump_psutil()

