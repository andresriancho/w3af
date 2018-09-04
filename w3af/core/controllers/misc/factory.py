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
from __future__ import print_function

import os
import sys
import warnings
import traceback

from w3af.core.controllers.exceptions import BaseFrameworkException
from w3af import ROOT_PATH


def factory(module_name, *args):
    """
    This function creates an instance of a class that's inside a module
    with the same name.

    Example :
    >>> spider = factory( 'w3af.plugins.crawl.google_spider' )
    >>> spider.get_name()
    'google_spider'


    :param module_name: Which plugin do you need?
    :return: An instance.
    """
    module_path = module_name.replace('.', '/')
    module_path = module_path.replace('w3af/', '')
    module_path = '%s.py' % module_path
    module_path = os.path.join(ROOT_PATH, module_path)

    if not os.path.exists(module_path):
        msg = 'The %s plugin does not exist.'
        raise BaseFrameworkException(msg % module_name)

    try:
        # https://github.com/andresriancho/w3af/issues/10705
        warnings.filterwarnings('ignore',
                                message='Not importing directory .*',
                                module='w3af.*')

        __import__(module_name)
    except SyntaxError:
        # Useful for development
        raise
    except ImportError:
        # Useful for development and users which failed to install all
        # dependencies
        #
        # https://github.com/andresriancho/w3af/issues/9688
        msg = ('It seems that your Python installation does not have all the'
               ' modules required by the w3af framework. For more information'
               ' about how to install and debug dependency issues please browse'
               ' to http://docs.w3af.org/en/latest/install.html')
        print(msg)

        # Raise so the user sees the whole traceback
        raise
    except Exception, e:
        msg = 'There was an error while importing %s: "%s".'
        raise BaseFrameworkException(msg % (module_name, e))

    # Now that we have the module imported get the class and instance
    class_name = module_name.split('.')[-1]

    try:
        module_inst = sys.modules[module_name]
        a_class = getattr(module_inst, class_name)
    except Exception:
        msg = ('The requested plugin (%s) does not have the expected format.'
               ' Our plugins need to define a class with the same name as the'
               ' module/file, in other words, if you name the module foo.py'
               ' there should be a "class foo(...):" inside that file.')
        raise BaseFrameworkException(msg % module_name)

    try:
        inst = a_class(*args)
    except Exception, e:
        msg = ('Failed to create an instance of "%s". The original exception'
               ' was: "%s". Traceback for this error:\n%s')
        msg = msg % (class_name, e, traceback.format_exc())
        raise BaseFrameworkException(msg)

    return inst
