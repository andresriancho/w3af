"""
cvss.py

Copyright 2017 Andres Riancho

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
import w3af.core.data.constants.severity as severity


def cvss_to_severity(cvss_score):
    """
    Convert CVSS score (1-10) to a w3af severity.

    :param cvss_score: CVSS score (1 to 10)
    :return: A severity
    """
    cvss_score = cvss_score * 10

    if cvss_score in range(20, 30):
        return severity.LOW
    elif cvss_score in range(30, 70):
        return severity.MEDIUM
    elif cvss_score in range(70, 100):
        return severity.HIGH

    return severity.INFORMATION
