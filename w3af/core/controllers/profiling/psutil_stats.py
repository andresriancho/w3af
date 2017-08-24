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
import sys
import json

from .utils.ps_mem import get_memory_usage, cmd_with_count
from .utils import get_filename_fmt, dump_data_every_thread, cancel_thread


PROFILING_OUTPUT_FMT = '/tmp/w3af-%s-%s.psutil'
DELAY_MINUTES = 2
SAVE_PSUTIL_PTR = []


def user_wants_psutil():
    _should_profile = os.environ.get('W3AF_PSUTILS', '0')

    if _should_profile.isdigit() and int(_should_profile) == 1:
        return True

    return False


if user_wants_psutil():
    try:
        # User's don't need this module
        import psutil
    except ImportError, ie:
        print('Failed to import psutil: %s' % ie)
        sys.exit(-1)


def should_dump_psutil(wrapped):
    def inner():
        if user_wants_psutil():
            return wrapped()

    return inner


@should_dump_psutil
def start_psutil_dump():
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

    # Get the memory usage from ps_mem
    pids_to_show = []
    for pid, pinfo in process_info.iteritems():
        exe = str(pinfo['exe'])
        if 'python' in exe and 'w3af' in exe:
            pids_to_show.append(pid)

    ps_mem_data = ps_mem_to_json(*get_memory_usage(pids_to_show, True))

    du_data = psutil.disk_usage(os.path.expanduser('~/.w3af'))
    disk_usage = {'total': get_human_readable_size(du_data.total),
                  'free': get_human_readable_size(du_data.free),
                  '% used': du_data.percent}

    # Merge all the data here
    psutil_data = {'CPU': psutil.cpu_times()._asdict(),
                   'Load average': os.getloadavg(),
                   'Virtual memory': psutil.virtual_memory()._asdict(),
                   'Swap memory': psutil.swap_memory()._asdict(),
                   'Network': netinfo,
                   'Processes': process_info,
                   'ps_mem': ps_mem_data,
                   'Disk IO counters': psutil.disk_io_counters(),
                   'Disk usage': disk_usage,
                   'Thread CPU usage': get_threads_cpu_percent()}
    
    json.dump(psutil_data, file(output_file, 'w'), indent=4, sort_keys=True)


def ps_mem_to_json(sorted_cmds, shareds, count, total):
    result = []
    
    for cmd in sorted_cmds:
        private = cmd[1] - shareds[cmd[0]]
        shared = shareds[cmd[0]]
        ram_used = cmd[1]
        cmd_count = cmd_with_count(cmd[0], count[cmd[0]])

        result.append({'Private': private,
                       'Shared': shared,
                       'Total RAM used': ram_used,
                       'Command line': cmd_count})

    return result


def get_threads_cpu_percent(interval=0.1):
    proc = psutil.Process()

    # pylint: disable=E1123
    # https://circleci.com/gh/andresriancho/w3af/1927
    total_percent = proc.get_cpu_percent(interval=interval)
    # pylint: enable=E1101

    total_time = sum(proc.cpu_times())

    result = {}
    for thread in proc.get_threads():
        thread_time = thread.system_time + thread.user_time
        thread_percent = total_percent * (thread_time/total_time)
        result[thread.id] = {'Thread total time': thread_time,
                             'Thread CPU usage %': thread_percent}

    return result


@should_dump_psutil
def stop_psutil_dump():
    """
    Save profiling information (if available)
    """
    cancel_thread(SAVE_PSUTIL_PTR)
    dump_psutil()


def get_human_readable_size(num):
    exp_str = [(0, 'B'), (10, 'KB'), (20, 'MB'), (30, 'GB'), (40, 'TB'), (50, 'PB')]
    i = 0
    while i+1 < len(exp_str) and num >= (2 ** exp_str[i+1][0]):
        i += 1
        rounded_val = round(float(num) / 2 ** exp_str[i][0], 2)
    return '%s %s' % (int(rounded_val), exp_str[i][1])
