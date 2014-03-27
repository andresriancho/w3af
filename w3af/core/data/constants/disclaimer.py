"""
disclaimer.py

Copyright 2012 Andres Riancho

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
# Heavily based on sqlmap's
DISCLAIMER = """Usage of w3af for sending any traffic to a target
 without prior mutual consent is illegal. It is the end user's responsibility to
 obey all applicable local, state and federal laws. Developers assume no liability
 and are not responsible for any misuse or damage caused by this program."""

DISCLAIMER = DISCLAIMER.replace('\n', '')
