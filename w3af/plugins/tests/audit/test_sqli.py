"""
test_sqli.py

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
from nose.plugins.attrib import attr

from w3af.plugins.tests.helper import PluginTest, PluginConfig
from w3af.core.controllers.ci.moth import get_moth_http
from w3af.core.controllers.ci.wavsep import get_wavsep_http
from w3af.core.controllers.ci.sqlmap_testenv import get_sqlmap_testenv_http


@attr('smoke')
class TestSQLI(PluginTest):

    target_url = get_moth_http('/audit/sql_injection/where_integer_qs.py')

    _run_configs = {
        'cfg': {
            'target': target_url + '?id=1',
            'plugins': {
                'audit': (PluginConfig('sqli'),),
            }
        }
    }

    def test_found_sqli(self):
        cfg = self._run_configs['cfg']
        self._scan(cfg['target'], cfg['plugins'])
        vulns = self.kb.get('sqli', 'sqli')
        
        self.assertEquals(1, len(vulns))

        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals("syntax error", vuln['error'])
        self.assertEquals("Unknown database", vuln['db'])
        self.assertEquals(self.target_url, str(vuln.get_url()))


class TestSQLMapTestEnv(PluginTest):

    base_path = '/sqlmap/mysql/'
    target_url = get_sqlmap_testenv_http(base_path)

    config = {
        'audit': (PluginConfig('sqli'),),

        'crawl': (PluginConfig('web_spider',
                               ('only_forward', True, PluginConfig.BOOL),
                               ('ignore_regex', '.*(asp|aspx)', PluginConfig.STR)),),
    }

    def test_found_sqli_in_testenv(self):
        """
        SqlMap's testenv is a rather strange test application since it doesn't
        have an index.html that defines the HTML forms to talk to the scripts
        which expect a POST request, so don't worry too much if those post_*
        are not found.
        """
        expected_path_param = {(u'get_str_like_par2.php', u'id'),
                               (u'get_dstr.php', u'id'),
                               (u'get_int_orderby.php', u'id'),
                               (u'get_str_brackets.php', u'id'),
                               (u'get_str.php', u'id'),
                               (u'get_int_inline.php', u'id'),
                               (u'get_str_like_par.php', u'id'),
                               (u'get_int.php', u'id'),
                               (u'get_int_rand.php', u'id'),
                               (u'get_int_having.php', u'id'),
                               (u'get_int_nolimit.php', u'id'),
                               (u'get_str_union.php', u'id'),
                               (u'get_str_like_par3.php', u'id'),
                               (u'get_int_user.php', u'id'),
                               (u'get_int_groupby.php', u'id'),
                               (u'get_int_blob.php', u'id'),
                               (u'get_dstr_like_par.php', u'id'),
                               (u'get_str_like.php', u'id'),
                               (u'get_dstr_like_par2.php', u'id'),
                               (u'get_int_filtered.php', u'id'),
                               (u'get_brackets.php', u'id'),
                               (u'get_int_limit.php', u'id'),
                               (u'get_int_limit_second.php', u'id')}

        #
        #   Now we assert the unknowns
        #
        ok_to_miss = {
            # Blind SQL injection
            u'get_int_noerror.php',
            u'get_str_noout.php',
            u'get_int_nooutput.php',
            u'get_str2.php',
            u'get_str_or.php',
            u'get_int_reflective.php',
            u'get_int_partialunion.php',

            # Blind SQL (time delay)
            u'get_int_benchmark.php',

            # Can't connect to local MySQL server through socket
            # '/var/run/mysqld/mysqld.sock' (2)
            u'get_int_substr.php',
            u'get_int_redirected.php',
            u'get_int_international.php',
            u'get_int_img.php',
            u'get_int_redirected_true.php',

            # Directories are OK to miss, they don't have vulns
            u'csrf/',
            u'csrf',

            u'iis',
            u'iis/',

            u'basic',
            u'digest',
            u'',

            # This one is not OK to miss, but we're missing it anyways
            # https://github.com/andresriancho/w3af/issues/12257
            u'csrf/post.php',
        }

        skip_startwith = {'post_', 'header_', 'referer_', 'cookie_'}
        kb_addresses = {('sqli', 'sqli')}

        self._scan_assert(self.config,
                          expected_path_param,
                          ok_to_miss,
                          kb_addresses,
                          skip_startwith)


class WAVSEPTest(PluginTest):
    config = {
        'audit': (PluginConfig('sqli'),
                  PluginConfig('blind_sqli')),

        'crawl': (PluginConfig('web_spider',
                               ('only_forward', True, PluginConfig.BOOL),
                               ('ignore_regex', '.*(asp|aspx)', PluginConfig.STR)),),
    }


class TestWAVSEPError(WAVSEPTest):

    base_path = ('/wavsep/active/SQL-Injection/'
                 'SInjection-Detection-Evaluation-GET-200Error/')

    target_url = get_wavsep_http(base_path)

    def test_found_sqli_wavsep_error(self):
        expected_path_param = {
            # These are detected using sql injection errors:
            (u'Case01-InjectionInLogin-String-LoginBypass-With200Errors.jsp', u'password'),
            (u'Case01-InjectionInLogin-String-LoginBypass-With200Errors.jsp', u'username'),
            (u'Case02-InjectionInSearch-String-UnionExploit-With200Errors.jsp', u'msg'),
            (u'Case03-InjectionInCalc-String-BooleanExploit-With200Errors.jsp', u'username'),
            (u'Case04-InjectionInUpdate-String-CommandInjection-With200Errors.jsp', u'msg'),
            (u'Case05-InjectionInSearchOrderBy-String-BinaryDeliberateRuntimeError-With200Errors.jsp', u'orderby'),
            (u'Case06-InjectionInView-Numeric-PermissionBypass-With200Errors.jsp', u'transactionId'),
            (u'Case07-InjectionInSearch-Numeric-UnionExploit-With200Errors.jsp', u'msgId'),
            (u'Case08-InjectionInCalc-Numeric-BooleanExploit-With200Errors.jsp', u'minBalanace'),
            (u'Case09-InjectionInUpdate-Numeric-CommandInjection-With200Errors.jsp', u'msgid'),
            (u'Case10-InjectionInSearchOrderBy-Numeric-BinaryDeliberateRuntimeError-With200Errors.jsp', u'orderby'),
            (u'Case11-InjectionInView-Date-PermissionBypass-With200Errors.jsp', u'transactionDate'),
            (u'Case12-InjectionInSearch-Date-UnionExploit-With200Errors.jsp', u'transactionDate'),
            (u'Case13-InjectionInCalc-Date-BooleanExploit-With200Errors.jsp', u'transactionDate'),
            (u'Case14-InjectionInUpdate-Date-CommandInjection-With200Errors.jsp', u'transactionDate'),

            # These are detected using blind SQL injection plugin:
            (u'Case15-InjectionInSearch-DateWithoutQuotes-UnionExploit-With200Errors.jsp', u'transactionDate'),
            (u'Case16-InjectionInView-NumericWithoutQuotes-PermissionBypass-With200Errors.jsp', u'transactionId'),
            (u'Case17-InjectionInSearch-NumericWithoutQuotes-UnionExploit-With200Errors.jsp', u'msgId'),
            (u'Case18-InjectionInCalc-NumericWithoutQuotes-BooleanExploit-With200Errors.jsp', u'minBalanace'),

            # Also with blind sql injection, but this is time delay:
            (u'Case19-InjectionInUpdate-NumericWithoutQuotes-CommandInjection-With200Errors.jsp', u'msgid')
        }

        # None is OK to miss -> 100% coverage
        ok_to_miss = set()
        skip_startwith = {'index.jsp'}
        kb_addresses = {('sqli', 'sqli'), ('blind_sqli', 'blind_sqli')}

        self._scan_assert(self.config,
                          expected_path_param,
                          ok_to_miss,
                          kb_addresses,
                          skip_startwith)


class TestWAVSEP500Error(WAVSEPTest):

    base_path = ('/wavsep/active/SQL-Injection/'
                 'SInjection-Detection-Evaluation-GET-500Error/')

    target_url = get_wavsep_http(base_path)

    def test_found_sqli_wavsep_error(self):
        expected_path_param = {
            (u'Case01-InjectionInLogin-String-LoginBypass-WithErrors.jsp', u'username'),
            (u'Case01-InjectionInLogin-String-LoginBypass-WithErrors.jsp', u'password'),
            (u'Case02-InjectionInSearch-String-UnionExploit-WithErrors.jsp', u'msg'),
            (u'Case03-InjectionInCalc-String-BooleanExploit-WithErrors.jsp', u'username'),
            (u'Case04-InjectionInUpdate-String-CommandInjection-WithErrors.jsp', u'msg'),
            (u'Case05-InjectionInSearchOrderBy-String-BinaryDeliberateRuntimeError-WithErrors.jsp', u'orderby'),
            (u'Case06-InjectionInView-Numeric-PermissionBypass-WithErrors.jsp', u'transactionId'),
            (u'Case07-InjectionInSearch-Numeric-UnionExploit-WithErrors.jsp', u'msgId'),
            (u'Case08-InjectionInCalc-Numeric-BooleanExploit-WithErrors.jsp', u'minBalanace'),
            (u'Case09-InjectionInUpdate-Numeric-CommandInjection-WithErrors.jsp', u'msgid'),
            (u'Case10-InjectionInSearchOrderBy-Numeric-BinaryDeliberateRuntimeError-WithErrors.jsp', u'orderby'),
            (u'Case11-InjectionInView-Date-PermissionBypass-WithErrors.jsp', u'transactionDate'),
            (u'Case12-InjectionInSearch-Date-UnionExploit-WithErrors.jsp', u'transactionDate'),
            (u'Case13-InjectionInCalc-Date-BooleanExploit-WithErrors.jsp', u'transactionDate'),
            (u'Case14-InjectionInUpdate-Date-CommandInjection-WithErrors.jsp', u'transactionDate'),
            (u'Case15-InjectionInSearch-DateWithoutQuotes-UnionExploit-WithErrors.jsp', u'transactionDate'),
            (u'Case16-InjectionInView-NumericWithoutQuotes-PermissionBypass-WithErrors.jsp', u'transactionId'),
            (u'Case17-InjectionInSearch-NumericWithoutQuotes-UnionExploit-WithErrors.jsp', u'msgId'),
            (u'Case18-InjectionInCalc-NumericWithoutQuotes-BooleanExploit-WithErrors.jsp', u'minBalanace'),
            (u'Case19-InjectionInUpdate-NumericWithoutQuotes-CommandInjection-WithErrors.jsp', u'msgid'),
        }

        # None is OK to miss -> 100% coverage
        ok_to_miss = set()
        skip_startwith = {'index.jsp'}
        kb_addresses = {('sqli', 'sqli'), ('blind_sqli', 'blind_sqli')}

        self._scan_assert(self.config,
                          expected_path_param,
                          ok_to_miss,
                          kb_addresses,
                          skip_startwith)


class TestWAVSEPWithDifferentiation(WAVSEPTest):

    base_path = ('/wavsep/active/SQL-Injection/'
                 'SInjection-Detection-Evaluation-GET-200Valid/')

    target_url = get_wavsep_http(base_path)

    def test_found_sqli_wavsep_differentiation(self):
        expected_path_param = {
            (u'Case01-InjectionInLogin-String-LoginBypass-WithDifferent200Responses.jsp', u'username'),
            (u'Case01-InjectionInLogin-String-LoginBypass-WithDifferent200Responses.jsp', u'password'),
            (u'Case02-InjectionInSearch-String-UnionExploit-WithDifferent200Responses.jsp', u'msg'),
            (u'Case03-InjectionInCalc-String-BooleanExploit-WithDifferent200Responses.jsp', u'username'),
            (u'Case04-InjectionInUpdate-String-CommandInjection-WithDifferent200Responses.jsp', u'msg'),
            (u'Case05-InjectionInSearchOrderBy-String-BinaryDeliberateRuntimeError-WithDifferent200Responses.jsp', u'orderby'),
            (u'Case06-InjectionInView-Numeric-PermissionBypass-WithDifferent200Responses.jsp', u'transactionId'),
            (u'Case07-InjectionInSearch-Numeric-UnionExploit-WithDifferent200Responses.jsp', u'msgId'),
            (u'Case08-InjectionInCalc-Numeric-BooleanExploit-WithDifferent200Responses.jsp', u'minBalanace'),
            (u'Case09-InjectionInUpdate-Numeric-CommandInjection-WithDifferent200Responses.jsp', u'msgid'),
            (u'Case10-InjectionInSearchOrderBy-Numeric-BinaryDeliberateRuntimeError-WithDifferent200Responses.jsp', u'orderby'),
            (u'Case11-InjectionInView-Date-PermissionBypass-WithDifferent200Responses.jsp', u'transactionDate'),
            (u'Case12-InjectionInSearch-Date-UnionExploit-WithDifferent200Responses.jsp', u'transactionDate'),
            (u'Case13-InjectionInCalc-Date-BooleanExploit-WithDifferent200Responses.jsp', u'transactionDate'),
            (u'Case14-InjectionInUpdate-Date-CommandInjection-WithDifferent200Responses.jsp', u'transactionDate'),
            (u'Case15-InjectionInSearch-DateWithoutQuotes-UnionExploit-WithDifferent200Responses.jsp', u'transactionDate'),
            (u'Case16-InjectionInView-NumericWithoutQuotes-PermissionBypass-WithDifferent200Responses.jsp', u'transactionId'),
            (u'Case17-InjectionInSearch-NumericWithoutQuotes-UnionExploit-WithDifferent200Responses.jsp', u'msgId'),
            (u'Case18-InjectionInCalc-NumericWithoutQuotes-BooleanExploit-WithDifferent200Responses.jsp', u'minBalanace'),
            (u'Case19-InjectionInUpdate-NumericWithoutQuotes-CommandInjection-WithDifferent200Responses.jsp', u'msgid'),
        }

        # None is OK to miss -> 100% coverage
        ok_to_miss = set()
        skip_startwith = {'index.jsp'}
        kb_addresses = {('sqli', 'sqli'), ('blind_sqli', 'blind_sqli')}

        self._scan_assert(self.config,
                          expected_path_param,
                          ok_to_miss,
                          kb_addresses,
                          skip_startwith)


class TestWAVSEPIdentical(WAVSEPTest):

    base_path = ('/wavsep/active/SQL-Injection/'
                 'SInjection-Detection-Evaluation-GET-200Identical/')

    target_url = get_wavsep_http(base_path)

    def test_found_sqli_wavsep_identical(self):
        expected_path_param = {
            (u'Case01-InjectionInView-Numeric-Blind-200ValidResponseWithDefaultOnException.jsp', u'transactionId'),
            (u'Case02-InjectionInView-String-Blind-200ValidResponseWithDefaultOnException.jsp', u'username'),
            (u'Case03-InjectionInView-Date-Blind-200ValidResponseWithDefaultOnException.jsp', u'transactionDate'),
            (u'Case04-InjectionInUpdate-Numeric-TimeDelayExploit-200Identical.jsp', u'transactionId'),
            (u'Case05-InjectionInUpdate-String-TimeDelayExploit-200Identical.jsp', u'description'),
            (u'Case06-InjectionInUpdate-Date-TimeDelayExploit-200Identical.jsp', u'transactionDate'),
            (u'Case07-InjectionInUpdate-NumericWithoutQuotes-TimeDelayExploit-200Identical.jsp', u'transactionId'),
            (u'Case08-InjectionInUpdate-DateWithoutQuotes-TimeDelayExploit-200Identical.jsp', u'transactionDate'),
        }

        # None is OK to miss -> 100% coverage
        ok_to_miss = {}
        skip_startwith = {'index.jsp'}
        kb_addresses = {('sqli', 'sqli'), ('blind_sqli', 'blind_sqli')}

        self._scan_assert(self.config,
                          expected_path_param,
                          ok_to_miss,
                          kb_addresses,
                          skip_startwith)


class TestWAVSEPExperimental(WAVSEPTest):

    base_path = ('/wavsep/active/SQL-Injection/'
                 'SInjection-Detection-Evaluation-GET-200Error-Experimental/')

    target_url = get_wavsep_http(base_path)

    def test_found_sqli_wavsep_experimental(self):
        expected_path_param = {
            (u'Case01-InjectionInInsertValues-String-BinaryDeliberateRuntimeError-With200Errors.jsp', u'target'),
            (u'Case01-InjectionInInsertValues-String-BinaryDeliberateRuntimeError-With200Errors.jsp', u'msg')
        }

        # None is OK to miss -> 100% coverage
        ok_to_miss = set()
        skip_startwith = {'index.jsp'}
        kb_addresses = {('sqli', 'sqli'), ('blind_sqli', 'blind_sqli')}

        self._scan_assert(self.config,
                          expected_path_param,
                          ok_to_miss,
                          kb_addresses,
                          skip_startwith)


class TestWAVSEPError500POST(WAVSEPTest):

    base_path = ('/wavsep/active/SQL-Injection/'
                 'SInjection-Detection-Evaluation-POST-500Error/')

    target_url = get_wavsep_http(base_path)

    def test_found_sqli_wavsep_error_500_post(self):
        expected_path_param = {
            (u'Case01-InjectionInLogin-String-LoginBypass-WithErrors.jsp', u'username'),
            (u'Case01-InjectionInLogin-String-LoginBypass-WithErrors.jsp', u'password'),
            (u'Case02-InjectionInSearch-String-UnionExploit-WithErrors.jsp', u'msg'),
            (u'Case03-InjectionInCalc-String-BooleanExploit-WithErrors.jsp', u'username'),
            (u'Case04-InjectionInUpdate-String-CommandInjection-WithErrors.jsp', u'msg'),
            (u'Case05-InjectionInSearchOrderBy-String-BinaryDeliberateRuntimeError-WithErrors.jsp', u'orderby'),
            (u'Case06-InjectionInView-Numeric-PermissionBypass-WithErrors.jsp', u'transactionId'),
            (u'Case07-InjectionInSearch-Numeric-UnionExploit-WithErrors.jsp', u'msgId'),
            (u'Case08-InjectionInCalc-Numeric-BooleanExploit-WithErrors.jsp', u'minBalanace'),
            (u'Case09-InjectionInUpdate-Numeric-CommandInjection-WithErrors.jsp', u'msgid'),
            (u'Case10-InjectionInSearchOrderBy-Numeric-BinaryDeliberateRuntimeError-WithErrors.jsp', u'orderby'),
            (u'Case11-InjectionInView-Date-PermissionBypass-WithErrors.jsp', u'transactionDate'),
            (u'Case12-InjectionInSearch-Date-UnionExploit-WithErrors.jsp', u'transactionDate'),
            (u'Case13-InjectionInCalc-Date-BooleanExploit-WithErrors.jsp', u'transactionDate'),
            (u'Case14-InjectionInUpdate-Date-CommandInjection-WithErrors.jsp', u'transactionDate'),
            (u'Case15-InjectionInSearch-DateWithoutQuotes-UnionExploit-WithErrors.jsp', u'transactionDate'),
            (u'Case16-InjectionInView-NumericWithoutQuotes-PermissionBypass-WithErrors.jsp', u'transactionId'),
            (u'Case17-InjectionInSearch-NumericWithoutQuotes-UnionExploit-WithErrors.jsp', u'msgId'),
            (u'Case18-InjectionInCalc-NumericWithoutQuotes-BooleanExploit-WithErrors.jsp', u'minBalanace'),
            (u'Case19-InjectionInUpdate-NumericWithoutQuotes-CommandInjection-WithErrors.jsp', u'msgid')}

        # None is OK to miss -> 100% coverage
        ok_to_miss = set()
        skip_startwith = {'index.jsp'}
        kb_addresses = {('sqli', 'sqli'), ('blind_sqli', 'blind_sqli')}

        self._scan_assert(self.config,
                          expected_path_param,
                          ok_to_miss,
                          kb_addresses,
                          skip_startwith)


class TestWAVSEPError200POST(WAVSEPTest):

    base_path = ('/wavsep/active/SQL-Injection/'
                 'SInjection-Detection-Evaluation-POST-200Error/')

    target_url = get_wavsep_http(base_path)

    def test_found_sqli_wavsep_error_200_post(self):
        expected_path_param = {
            (u'Case01-InjectionInLogin-String-LoginBypass-With200Errors.jsp', u'password'),
            (u'Case01-InjectionInLogin-String-LoginBypass-With200Errors.jsp', u'username'),
            (u'Case02-InjectionInSearch-String-UnionExploit-With200Errors.jsp', u'msg'),
            (u'Case03-InjectionInCalc-String-BooleanExploit-With200Errors.jsp', u'username'),
            (u'Case04-InjectionInUpdate-String-CommandInjection-With200Errors.jsp', u'msg'),
            (u'Case05-InjectionInSearchOrderBy-String-BinaryDeliberateRuntimeError-With200Errors.jsp', u'orderby'),
            (u'Case06-InjectionInView-Numeric-PermissionBypass-With200Errors.jsp', u'transactionId'),
            (u'Case07-InjectionInSearch-Numeric-UnionExploit-With200Errors.jsp', u'msgId'),
            (u'Case08-InjectionInCalc-Numeric-BooleanExploit-With200Errors.jsp', u'minBalanace'),
            (u'Case09-InjectionInUpdate-Numeric-CommandInjection-With200Errors.jsp', u'msgid'),
            (u'Case10-InjectionInSearchOrderBy-Numeric-BinaryDeliberateRuntimeError-With200Errors.jsp', u'orderby'),
            (u'Case11-InjectionInView-Date-PermissionBypass-With200Errors.jsp', u'transactionDate'),
            (u'Case12-InjectionInSearch-Date-UnionExploit-With200Errors.jsp', u'transactionDate'),
            (u'Case13-InjectionInCalc-Date-BooleanExploit-With200Errors.jsp', u'transactionDate'),
            (u'Case14-InjectionInUpdate-Date-CommandInjection-With200Errors.jsp', u'transactionDate'),
            (u'Case15-InjectionInSearch-DateWithoutQuotes-UnionExploit-With200Errors.jsp', u'transactionDate'),
            (u'Case16-InjectionInView-NumericWithoutQuotes-PermissionBypass-With200Errors.jsp', u'transactionId'),
            (u'Case17-InjectionInSearch-NumericWithoutQuotes-UnionExploit-With200Errors.jsp', u'msgId'),
            (u'Case18-InjectionInCalc-NumericWithoutQuotes-BooleanExploit-With200Errors.jsp', u'minBalanace'),
            (u'Case19-InjectionInUpdate-NumericWithoutQuotes-CommandInjection-With200Errors.jsp', u'msgid'),
        }

        # None is OK to miss -> 100% coverage
        ok_to_miss = set()
        skip_startwith = {'index.jsp'}
        kb_addresses = {('sqli', 'sqli'), ('blind_sqli', 'blind_sqli')}

        self._scan_assert(self.config,
                          expected_path_param,
                          ok_to_miss,
                          kb_addresses,
                          skip_startwith)


class TestWAVSEPWithDifferentiationPOST(WAVSEPTest):

    base_path = ('/wavsep/active/SQL-Injection/'
                 'SInjection-Detection-Evaluation-POST-200Valid/')

    target_url = get_wavsep_http(base_path)

    def test_found_sqli_wavsep_differentiation_post(self):
        expected_path_param = {
            (u'Case01-InjectionInLogin-String-LoginBypass-WithDifferent200Responses.jsp', u'username'),
            (u'Case01-InjectionInLogin-String-LoginBypass-WithDifferent200Responses.jsp', u'password'),
            (u'Case02-InjectionInSearch-String-UnionExploit-WithDifferent200Responses.jsp', u'msg'),
            (u'Case03-InjectionInCalc-String-BooleanExploit-WithDifferent200Responses.jsp', u'username'),
            (u'Case04-InjectionInUpdate-String-CommandInjection-WithDifferent200Responses.jsp', u'msg'),
            (u'Case05-InjectionInSearchOrderBy-String-BinaryDeliberateRuntimeError-WithDifferent200Responses.jsp', u'orderby'),
            (u'Case06-InjectionInView-Numeric-PermissionBypass-WithDifferent200Responses.jsp', u'transactionId'),
            (u'Case07-InjectionInSearch-Numeric-UnionExploit-WithDifferent200Responses.jsp', u'msgId'),
            (u'Case08-InjectionInCalc-Numeric-BooleanExploit-WithDifferent200Responses.jsp', u'minBalanace'),
            (u'Case09-InjectionInUpdate-Numeric-CommandInjection-WithDifferent200Responses.jsp', u'msgid'),
            (u'Case10-InjectionInSearchOrderBy-Numeric-BinaryDeliberateRuntimeError-WithDifferent200Responses.jsp', u'orderby'),
            (u'Case11-InjectionInView-Date-PermissionBypass-WithDifferent200Responses.jsp', u'transactionDate'),
            (u'Case12-InjectionInSearch-Date-UnionExploit-WithDifferent200Responses.jsp', u'transactionDate'),
            (u'Case13-InjectionInCalc-Date-BooleanExploit-WithDifferent200Responses.jsp', u'transactionDate'),
            (u'Case14-InjectionInUpdate-Date-CommandInjection-WithDifferent200Responses.jsp', u'transactionDate'),
            (u'Case15-InjectionInSearch-DateWithoutQuotes-UnionExploit-WithDifferent200Responses.jsp', u'transactionDate'),
            (u'Case16-InjectionInView-NumericWithoutQuotes-PermissionBypass-WithDifferent200Responses.jsp', u'transactionId'),
            (u'Case17-InjectionInSearch-NumericWithoutQuotes-UnionExploit-WithDifferent200Responses.jsp', u'msgId'),
            (u'Case18-InjectionInCalc-NumericWithoutQuotes-BooleanExploit-WithDifferent200Responses.jsp', u'minBalanace'),
            (u'Case19-InjectionInUpdate-NumericWithoutQuotes-CommandInjection-WithDifferent200Responses.jsp', u'msgid'),
        }

        # None is OK to miss -> 100% coverage
        ok_to_miss = set()
        skip_startwith = {'index.jsp'}
        kb_addresses = {('sqli', 'sqli'), ('blind_sqli', 'blind_sqli')}

        self._scan_assert(self.config,
                          expected_path_param,
                          ok_to_miss,
                          kb_addresses,
                          skip_startwith)


class TestWAVSEPIdenticalPOST(WAVSEPTest):

    base_path = ('/wavsep/active/SQL-Injection/'
                 'SInjection-Detection-Evaluation-POST-200Identical/')

    target_url = get_wavsep_http(base_path)

    def test_found_sqli_wavsep_identical_post(self):
        expected_path_param = {
            (u'Case01-InjectionInView-Numeric-Blind-200ValidResponseWithDefaultOnException.jsp', u'transactionId'),
            (u'Case02-InjectionInView-String-Blind-200ValidResponseWithDefaultOnException.jsp', u'username'),
            (u'Case03-InjectionInView-Date-Blind-200ValidResponseWithDefaultOnException.jsp', u'transactionDate'),
            (u'Case04-InjectionInUpdate-Numeric-TimeDelayExploit-200Identical.jsp', u'transactionId'),
            (u'Case05-InjectionInUpdate-String-TimeDelayExploit-200Identical.jsp', u'description'),
            (u'Case06-InjectionInUpdate-Date-TimeDelayExploit-200Identical.jsp', u'transactionDate'),
            (u'Case07-InjectionInUpdate-NumericWithoutQuotes-TimeDelayExploit-200Identical.jsp', u'transactionId'),
            (u'Case08-InjectionInUpdate-DateWithoutQuotes-TimeDelayExploit-200Identical.jsp', u'transactionDate'),
        }

        # None is OK to miss -> 100% coverage
        ok_to_miss = set()
        skip_startwith = {'index.jsp'}
        kb_addresses = {('sqli', 'sqli'), ('blind_sqli', 'blind_sqli')}

        self._scan_assert(self.config,
                          expected_path_param,
                          ok_to_miss,
                          kb_addresses,
                          skip_startwith)


class TestWAVSEPExperimentalPOST(WAVSEPTest):

    base_path = ('/wavsep/active/SQL-Injection/'
                 'SInjection-Detection-Evaluation-POST-200Error-Experimental/')

    target_url = get_wavsep_http(base_path)

    def test_found_sqli_wavsep_experimental_post(self):
        expected_path_param = {
            (u'Case01-InjectionInInsertValues-String-BinaryDeliberateRuntimeError-With200Errors.jsp', u'target'),
            (u'Case01-InjectionInInsertValues-String-BinaryDeliberateRuntimeError-With200Errors.jsp', u'msg')
        }

        # None is OK to miss -> 100% coverage
        ok_to_miss = set()
        skip_startwith = {'index.jsp'}
        kb_addresses = {('sqli', 'sqli'), ('blind_sqli', 'blind_sqli')}

        self._scan_assert(self.config,
                          expected_path_param,
                          ok_to_miss,
                          kb_addresses,
                          skip_startwith)