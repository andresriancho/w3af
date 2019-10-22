"""
form_constants.py

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

DEFAULT_FORM_ENCODING = 'application/x-www-form-urlencoded'

INPUT_TYPE_FILE = 'file'
INPUT_TYPE_CHECKBOX = 'checkbox'
INPUT_TYPE_RADIO = 'radio'
INPUT_TYPE_TEXT = 'text'
INPUT_TYPE_HIDDEN = 'hidden'
INPUT_TYPE_SUBMIT = 'submit'
INPUT_TYPE_SELECT = 'select'
INPUT_TYPE_PASSWD = 'password'

# Not exactly an <input>, but close enough:
INPUT_TYPE_TEXTAREA = 'textarea'

ALL_INPUT_TYPES = (INPUT_TYPE_FILE,
                   INPUT_TYPE_CHECKBOX,
                   INPUT_TYPE_RADIO,
                   INPUT_TYPE_TEXT,
                   INPUT_TYPE_HIDDEN,
                   INPUT_TYPE_SUBMIT,
                   INPUT_TYPE_SELECT,
                   INPUT_TYPE_PASSWD)

MODE_ALL = 'all'
MODE_TB = 'tb'
MODE_TMB = 'tmb'
MODE_T = 't'
MODE_B = 'b'
