# -*- coding: utf8 -*-
"""
test_github_issues.py

Copyright 2013 Andres Riancho

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

from github import Github
from nose.plugins.attrib import attr

from w3af.core.controllers.easy_contribution.github_issues import (GithubIssues,
                                                                   OAUTH_TOKEN,
                                                                   OAuthTokenInvalid,
                                                                   UserCredentialsInvalid)


@attr('internet')
class TestGithubIssues(unittest.TestCase):

    def test_report(self):
        gh = GithubIssues(OAUTH_TOKEN)
        gh.login()
        
        summary = 'Unittest bug report'
        userdesc = 'Please remove this ticket'

        ticket_id, ticket_url = gh.report_bug(summary, userdesc)
        self.assertIsInstance(ticket_id, int)
        self.assertTrue(ticket_url.startswith(
            'https://github.com/andresriancho/w3af/issues/'))
        
        # Remove the ticket I've just created
        gh = Github(OAUTH_TOKEN)
        repo = gh.get_user('andresriancho').get_repo('w3af')
        issue = repo.get_issue(ticket_id)
        issue.edit(state='closed')

    def test_login_failed_token(self):
        gh = GithubIssues(OAUTH_TOKEN + 'foobar')
        self.assertRaises(OAuthTokenInvalid, gh.login)

    def test_login_success_token(self):
        gh = GithubIssues(OAUTH_TOKEN)
        self.assertTrue(gh.login())
    
    def test_login_failed_user_pass(self):
        gh = GithubIssues('foobar', 'testbar')
        self.assertRaises(UserCredentialsInvalid, gh.login)
