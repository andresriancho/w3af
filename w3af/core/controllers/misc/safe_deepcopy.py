"""
safe_deepcopy.py

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
import copy

from w3af.core.controllers.misc.decorators import retry


@retry(2, delay=0.5, backoff=1.1)
def safe_deepcopy(instance):
    """
    In most cases this will just be a wrapper around copy.deepcopy(instance)
    without any added features, but when that fails because of a race condition
    such as dictionary changed size during iteration - crawl_plugin.py #8956 ,
    then we retry.

    I don't want to debug the real issue since it only happen once and I can
    live with the retry.

    :see: https://github.com/andresriancho/w3af/issues/8956
    :see: https://github.com/andresriancho/w3af/issues/9449

    :param instance: The object instance we want to copy
    :return: A deep copy of the instance
    """
    return copy.deepcopy(instance)