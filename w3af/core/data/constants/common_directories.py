"""
common_directories.py

Copyright 2008 Andres Riancho

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


def get_common_directories(os=None):
    """
    :param os: The operating system for which we want the common directories.
    If no os is specified, all directories are returned.

    :return: A list of common directories
    """
    directories = []

    if os == 'linux' or os is None:
        directories.append("/bin/")
        directories.append("/boot/")
        directories.append("/cdrom/")
        directories.append("/dev/")
        directories.append("/etc/")
        directories.append("/home/")
        directories.append("/initrd/")
        directories.append("/lib/")
        directories.append("/media/")
        directories.append("/mnt/")
        directories.append("/opt/")
        directories.append("/proc/")
        directories.append("/root/")
        directories.append("/sbin/")
        directories.append("/sys/")
        directories.append("/srv/")
        directories.append("/tmp/")
        directories.append("/usr/")
        directories.append("/var/")
        directories.append("/htdocs/")

    if os == 'windows' or os is None:
        directories.append(r"C:\\")
        directories.append(r"D:\\")
        directories.append(r"E:\\")
        directories.append(r"Z:\\")
        directories.append(r"C:\\windows\\")
        directories.append(r"C:\\winnt\\")
        directories.append(r"C:\\win32\\")
        directories.append(r"C:\\win\\system\\")
        directories.append(r"C:\\windows\\system\\")
        directories.append(r"C:\\winnt\\system\\")
        directories.append(r"C:\\win32\\system\\")
        directories.append(r"C:\\Program Files\\")
        directories.append(r"C:\\Documents and Settings\\")

    return directories
