# -*- coding: UTF-8 -*-
"""
test_profile.py

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
import unittest

from nose.plugins.attrib import attr

from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.controllers.exceptions import BaseFrameworkException


class TestCoreProfiles(unittest.TestCase):

    @attr('smoke')
    def test_use_profile(self):
        w3af_core = w3afCore()
        w3af_core.profiles.use_profile('OWASP_TOP10', workdir='.')

        enabled_plugins = w3af_core.plugins.get_all_enabled_plugins()

        self.assertTrue('sqli' in enabled_plugins['audit'])
        self.assertTrue('credit_cards' in enabled_plugins['grep'])
        self.assertTrue('private_ip' in enabled_plugins['grep'])
        self.assertTrue('dns_wildcard' in enabled_plugins['infrastructure'])
        self.assertTrue('web_spider' in enabled_plugins['crawl'])

    def test_save_current_to_new_profile(self):
        w3af_core = w3afCore()
        w3af_core.profiles.use_profile('OWASP_TOP10', workdir='.')

        audit = w3af_core.plugins.get_enabled_plugins('audit')
        disabled_plugin = audit[-1]
        audit = audit[:-1]
        w3af_core.plugins.set_plugins(audit, 'audit')
        enabled = w3af_core.plugins.get_enabled_plugins('audit')
        self.assertEquals(set(enabled), set(audit))
        self.assertTrue(disabled_plugin not in enabled)

        w3af_core.profiles.save_current_to_new_profile('unittest-OWASP_TOP10')

        # Get a new, clean instance of the core.
        w3af_core = w3afCore()
        audit = w3af_core.plugins.get_enabled_plugins('audit')
        self.assertEquals(audit, [])

        w3af_core.profiles.use_profile('unittest-OWASP_TOP10')
        enabled_plugins = w3af_core.plugins.get_all_enabled_plugins()

        self.assertTrue(disabled_plugin not in enabled_plugins['audit'])
        self.assertTrue('credit_cards' in enabled_plugins['grep'])
        self.assertTrue('private_ip' in enabled_plugins['grep'])
        self.assertTrue('dns_wildcard' in enabled_plugins['infrastructure'])
        self.assertTrue('web_spider' in enabled_plugins['crawl'])

        w3af_core.profiles.remove_profile('unittest-OWASP_TOP10')

    def test_remove_profile(self):
        w3af_core = w3afCore()
        w3af_core.profiles.save_current_to_new_profile('unittest-remove')
        w3af_core.profiles.remove_profile('unittest-remove')

        self.assertRaises(
            BaseFrameworkException, w3af_core.profiles.use_profile, 'unittest-remove')

    def test_remove_profile_not_exists(self):
        w3af_core = w3afCore()
        self.assertRaises(
            BaseFrameworkException, w3af_core.profiles.remove_profile, 'not-exists')

    @attr('smoke')
    def test_use_all_profiles(self):
        """
        This test catches the errors in my profiles that generate these messages:

        ***************************************************************************
        The profile you are trying to load (web_infrastructure) seems to be outdated,
        this is a common issue which happens when the framework is updated and one of
        its plugins adds/removes one of the configuration parameters referenced by a
        profile, or the plugin is removed all together.

        The profile was loaded but some of your settings might have been lost.
        This is the list of issues that were found:

        - Setting the options for plugin "infrastructure.server_header" raised
        an exception due to unknown configuration parameters.

        We recommend you review the specific plugin configurations, apply the
        required changes and save the profile in order to update it and avoid
        this message. If this warning does not disappear you can manually edit
        the profile file to fix it.
        ***************************************************************************
        """
        w3af_core = w3afCore()
        valid, invalid = w3af_core.profiles.get_profile_list('.')

        self.assertTrue(len(valid) > 5)
        self.assertEqual(len(invalid), 0)

        for profile_inst in valid:
            profile_name = profile_inst.get_name()

            w3af_core.profiles.use_profile(profile_name, workdir='.')

    def test_cant_start_new_thread_bug(self):
        """
        This tests that https://github.com/andresriancho/w3af/issues/56 was
        properly fixed after the change in how sqlite threads were managed.
        """
        w3af_core = w3afCore()
        valid, _ = w3af_core.profiles.get_profile_list('.')

        for _ in xrange(10):
            for profile_inst in valid:
                profile_name = profile_inst.get_name()

                w3af_core.profiles.use_profile(profile_name, workdir='.')
