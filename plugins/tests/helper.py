'''
helper.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

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
'''

from itertools import chain
import os
import unittest

from core.controllers.w3afCore import w3afCore
from core.controllers.misc.homeDir import W3AF_LOCAL_PATH
from core.data.options.option import option as Option
from core.data.options.comboOption import comboOption as ComboOption
from core.data.options.optionList import optionList as OptionList
import core.data.kb.knowledgeBase as kb

os.chdir(W3AF_LOCAL_PATH)

class PluginTest(unittest.TestCase):
    
    runconfig = {}
    kb = kb.kb
    
    def _scan(self, target, plugins):
        '''
        Setup env and start scan. Typically called from children's
        test methods.
        
        @param target: The target to scan.
        @param plugins: PluginConfig objects to activate and setup before
            the test runs.
        '''
        def _targetoptions(*target):
            opts = OptionList()
            
            opt = Option('target', '', '', Option.LIST)
            opt.setValue(','.join(target))
            opts.add(opt)
            opt = ComboOption(
                      'targetOS', ('unknown','unix','windows'), '', 'combo')
            opts.add(opt)
            opt = ComboOption(
                      'targetFramework',
                      ('unknown', 'php','asp', 'asp.net',
                       'java','jsp','cfm','ruby','perl'),
                      '', 'combo'
                      )
            opts.add(opt)
            return opts
            
        self.w3afcore = w3afCore()
        # Set target(s)
        if isinstance(target, basestring):
            target = (target,)
        self.w3afcore.target.setOptions(_targetoptions(*target))
        # Enable plugins to be tested
        for ptype, plugincfgs in plugins.items():
            self.w3afcore.setPlugins([p.name for p in plugincfgs], ptype)
            for pcfg in plugincfgs:
                self.w3afcore.setPluginOptions(ptype, pcfg.name, pcfg.options)
        # Verify env and start the scan
        self.w3afcore.initPlugins()
        self.w3afcore.verifyEnvironment()
        self.w3afcore.start()
    
    def tearDown(self):
        self.w3afcore.quit()
        self.kb.cleanup()


class OptionDict(dict):
    def __missing__(self, key):
        opt = Option(key, u'', '', Option.STRING)
        self[key] = opt
        return opt


class PluginConfig(object):
    
    BOOL = 'boolean'
    STR = 'string'
    LIST = 'list'
    INT = 'integer'
    
    def __init__(self, name, *opts):
        self._name = name
        self._options = OptionDict()
        for optname, optval, optty in opts:
            self._options[optname] = Option(optname, optval, '', optty)
    
    @property
    def name(self):
        return self._name
    
    @property
    def options(self):
        return self._options