#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import cPickle

# Need this hack in order to be able to re-add the current path to the
# python-path, since running a script seems to change it (?)
sys.path.insert(0, os.path.abspath(os.curdir))

from w3af.core.controllers.ci.nosetests_wrapper.utils.test_stats import get_test_ids
from w3af.core.controllers.ci.nosetests_wrapper.constants import ID_FILE, NOSE_RUN_SELECTOR


def nose_strategy():
    """
    :return: A list with the nosetests commands to run.
    """
    # This will generate the ID_FILE
    get_test_ids(NOSE_RUN_SELECTOR)
    nose_data = cPickle.load(file(ID_FILE))

    for key, value in nose_data['ids'].iteritems():
        _, _, test_class_method = value
        print('%s:%s' % (key, test_class_method))


if __name__ == '__main__':
    nose_strategy()
