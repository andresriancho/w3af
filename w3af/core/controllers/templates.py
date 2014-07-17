"""
template.py

Copyright 2006 Andres Riancho

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
from jinja2 import Environment, FileSystemLoader
from w3af import ROOT_PATH

_default_env = Environment(loader=FileSystemLoader(os.path.join(ROOT_PATH,
                                                                'templates')))


def render(template, context=None, env=None):
    """Render template with name template and context
    if env is not set, then _default_env is used

    :param template: string path to template, relative to templates folder
    :param context: dict with variables
    :return: compiled template string
    """
    if env is None:
        env = _default_env
    tmpl = env.get_template(template)
    if context is None:
        context = {}
    return tmpl.render(context)
