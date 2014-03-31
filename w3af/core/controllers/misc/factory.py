"""
factory.py

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
import sys
import traceback

from w3af.core.controllers.exceptions import BaseFrameworkException


def factory(module_name, *args):
    """
    This function creates an instance of a class thats inside a module
    with the same name.

    Example :
    >>> spider = factory( 'w3af.plugins.crawl.google_spider' )
    >>> spider.get_name()
    'google_spider'


    :param module_name: Which plugin do you need?
    :return: An instance.
    """
    try:
        __import__(module_name)
    except ImportError, ie:
        msg = 'There was an error while importing %s: "%s".'
        raise BaseFrameworkException(msg % (module_name, ie))
    except Exception, e:
        msg = 'There was an error while importing %s: "%s".'
        raise BaseFrameworkException(msg % (module_name, e))
    else:

        class_name = module_name.split('.')[-1]

        try:
            module_inst = sys.modules[module_name]
            a_class = getattr(module_inst, class_name)
        except Exception, e:
            msg = 'The requested plugin ("%s") doesn\'t have a correct format: "%s".'
            raise BaseFrameworkException(msg % (module_name, e))
        else:
            try:
                inst = a_class(*args)
            except Exception, e:
                msg = 'Failed to get an instance of "%s". Original exception: '
                msg += '"%s". Traceback for this error: %s'
                raise BaseFrameworkException(
                    msg % (class_name, e, traceback.format_exc()))
            return inst
