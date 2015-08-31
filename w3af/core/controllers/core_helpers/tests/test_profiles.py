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
import os

from ConfigParser import ConfigParser
from nose.plugins.attrib import attr

from w3af import ROOT_PATH
from w3af.core.data.profile.profile import profile
from w3af.core.controllers.w3afCore import w3afCore
from w3af.core.controllers.exceptions import BaseFrameworkException


class TestCoreProfiles(unittest.TestCase):

    INPUT_FILE = os.path.relpath(os.path.join(ROOT_PATH, 'plugins', 'audit',
                                              'ssl_certificate', 'ca.pem'))

    def setUp(self):
        super(TestCoreProfiles, self).setUp()
        self.core = w3afCore()

    def tearDown(self):
        super(TestCoreProfiles, self).tearDown()
        self.core.worker_pool.terminate_join()

    @attr('smoke')
    def test_use_profile(self):
        self.core.profiles.use_profile('OWASP_TOP10', workdir='.')

        enabled_plugins = self.core.plugins.get_all_enabled_plugins()

        self.assertIn('sqli', enabled_plugins['audit'])
        self.assertIn('credit_cards', enabled_plugins['grep'])
        self.assertIn('private_ip', enabled_plugins['grep'])
        self.assertIn('dns_wildcard', enabled_plugins['infrastructure'])
        self.assertIn('web_spider', enabled_plugins['crawl'])

    def test_save_current_to_new_profile(self):
        self.core.profiles.use_profile('OWASP_TOP10', workdir='.')

        audit = self.core.plugins.get_enabled_plugins('audit')
        disabled_plugin = audit[-1]
        audit = audit[:-1]
        self.core.plugins.set_plugins(audit, 'audit')
        enabled = self.core.plugins.get_enabled_plugins('audit')
        self.assertEquals(set(enabled), set(audit))
        self.assertTrue(disabled_plugin not in enabled)

        new_profile_name = 'save-current-new'
        self.core.profiles.save_current_to_new_profile(new_profile_name)

        # Get a new, clean instance of the core.
        clean_core = w3afCore()
        audit = clean_core.plugins.get_enabled_plugins('audit')
        self.assertEquals(audit, [])

        clean_core.profiles.use_profile(new_profile_name)
        enabled_plugins = clean_core.plugins.get_all_enabled_plugins()

        self.assertNotIn(disabled_plugin, enabled_plugins['audit'])
        self.assertIn('credit_cards', enabled_plugins['grep'])
        self.assertIn('private_ip', enabled_plugins['grep'])
        self.assertIn('dns_wildcard', enabled_plugins['infrastructure'])
        self.assertIn('web_spider', enabled_plugins['crawl'])

        # cleanup
        clean_core.profiles.remove_profile(new_profile_name)
        clean_core.worker_pool.terminate_join()

    def test_remove_profile(self):
        self.core.profiles.save_current_to_new_profile('unittest-remove')
        self.core.profiles.remove_profile('unittest-remove')

        self.assertRaises(BaseFrameworkException,
                          self.core.profiles.use_profile,
                          'unittest-remove')

    def test_remove_profile_not_exists(self):
        self.assertRaises(BaseFrameworkException,
                          self.core.profiles.remove_profile,
                          'not-exists')

    @attr('smoke')
    def test_use_all_profiles(self):
        """
        This test catches the errors in my profiles that generate these
        messages:

        ************************************************************************
        The profile you are trying to load (web_infrastructure) seems to be
        outdated, this is a common issue which happens when the framework is
        updated and one of its plugins adds/removes one of the configuration
        parameters referenced by a profile, or the plugin is removed all
        together.

        The profile was loaded but some of your settings might have been lost.
        This is the list of issues that were found:

        - Setting the options for plugin "infrastructure.server_header" raised
        an exception due to unknown configuration parameters.

        We recommend you review the specific plugin configurations, apply the
        required changes and save the profile in order to update it and avoid
        this message. If this warning does not disappear you can manually edit
        the profile file to fix it.
        ************************************************************************
        """
        valid, invalid = self.core.profiles.get_profile_list('.')

        self.assertTrue(len(valid) > 5)
        self.assertEqual(len(invalid), 0)

        for profile_inst in valid:
            profile_name = profile_inst.get_name()

            self.core.profiles.use_profile(profile_name, workdir='.')

    def test_cant_start_new_thread_bug(self):
        """
        This tests that https://github.com/andresriancho/w3af/issues/56 was
        properly fixed after the change in how sqlite threads were managed.
        """
        valid, _ = self.core.profiles.get_profile_list('.')

        for _ in xrange(10):
            for profile_inst in valid:
                profile_name = profile_inst.get_name()

                self.core.profiles.use_profile(profile_name, workdir='.')

    def test_use_profile_variable_replace(self):
        self.core.profiles.use_profile('OWASP_TOP10', workdir='.')

        plugin_opts = self.core.plugins.get_plugin_options('audit',
                                                           'ssl_certificate')
        ca_path = plugin_opts['caFileName'].get_value()
        self.assertEqual(ca_path, self.INPUT_FILE)

    def test_load_save_as_no_changes(self):
        """
        During some tests I noticed that the console UI was removing the plugin
        configuration from the profiles when I did a save_as, so this test
        is rather simple and will:

            * Load a profile
            * Save it again
            * Make a diff between the old and new, it should be empty
        """
        self.core.profiles.use_profile('OWASP_TOP10', workdir='.')
        self.core.profiles.save_current_to_new_profile('unittest-OWASP_TOP10')

        # Diff the two profile files
        p1 = profile('OWASP_TOP10', workdir='.')
        p2 = profile('unittest-OWASP_TOP10', workdir='.')

        assertProfilesEqual(p1.profile_file_name, p2.profile_file_name)

        # cleanup
        self.core.profiles.remove_profile('unittest-OWASP_TOP10')


def assertProfilesEqual(profile_filename_a, profile_filename_b,
                        skip_sections=None, skip_options=None):
    """
    Compares two profiles
    """
    if skip_options is None:
        skip_options = {'local_ip_address', 'description', 'name'}

    if skip_sections is None:
        skip_sections = {'target'}

    original = ConfigParser()
    original.read(profile_filename_a)

    saved = ConfigParser()
    saved.read(profile_filename_b)

    #
    #   Analyze in one way
    #
    for section_name in original.sections():
        for orig_name, orig_value in original.items(section_name):
            if orig_name in skip_options:
                continue

            if section_name in skip_sections:
                continue

            saved_value = saved.get(section_name, orig_name)
            msg = ('The "%s" option of the "%s" section changed from'
                   ' "%s" to "%s"')
            args = (orig_name, section_name, orig_value, saved_value)
            assert saved_value == orig_value, msg % args

    #
    #   And then the other
    #
    for section_name in saved.sections():
        for saved_name, saved_value in saved.items(section_name):
            if saved_name in skip_options:
                continue

            if section_name in skip_sections:
                continue

            orig_value = original.get(section_name, saved_name)
            msg = ('The "%s" option of the "%s" section changed from'
                   ' "%s" to "%s"')
            args = (saved_name, section_name, orig_value, saved_value)
            assert saved_value == orig_value, msg % args