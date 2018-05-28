"""
test_knowledge_base.py

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
import copy
import uuid
import unittest

from mock import Mock

from w3af.core.controllers.threads.threadpool import Pool
from w3af.core.controllers.exceptions import DBException
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.kb.knowledge_base import kb, DBKnowledgeBase
from w3af.core.data.kb.tests.test_info import MockInfo
from w3af.core.data.kb.tests.test_vuln import MockVuln
from w3af.core.data.kb.shell import Shell
from w3af.core.data.kb.info_set import InfoSet
from w3af.core.data.dc.query_string import QueryString
from w3af.core.data.db.dbms import get_default_persistent_db_instance
from w3af.core.data.url.extended_urllib import ExtendedUrllib
from w3af.core.data.fuzzer.mutants.querystring_mutant import QSMutant
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.controllers.w3afCore import w3afCore
from w3af.plugins.attack.payloads.shell_handler import get_shell_code
from w3af.plugins.attack.sqlmap import SQLMapShell
from w3af.plugins.attack.db.sqlmap_wrapper import Target, SQLMapWrapper
from w3af.plugins.attack.dav import DAVShell
from w3af.plugins.attack.eval import EvalShell
from w3af.plugins.attack.file_upload import FileUploadShell
from w3af.plugins.attack.local_file_reader import FileReaderShell
from w3af.plugins.attack.rfi import RFIShell, PortScanShell
from w3af.plugins.attack.xpath import XPathReader, IsErrorResponse
from w3af.plugins.attack.os_commanding import (OSCommandingShell,
                                               BasicExploitStrategy)


class TestKnowledgeBase(unittest.TestCase):

    def setUp(self):
        kb.cleanup()

    def test_basic(self):
        kb.raw_write('a', 'b', 'c')
        data = kb.raw_read('a', 'b')
        self.assertEqual(data, 'c')

    def test_default_get(self):
        self.assertEqual(kb.get('a', 'b'), [])
    
    def test_default_raw_read(self):
        self.assertEqual(kb.raw_read('a', 'b'), [])

    def test_raw_read_error(self):
        kb.append('a', 'b', MockInfo())
        kb.append('a', 'b', MockInfo())
        self.assertRaises(RuntimeError, kb.raw_read,'a', 'b')

    def test_default_first_saved(self):
        kb.raw_write('a', 'b', 'c')
        self.assertEqual(kb.get('a', 'not-exist'), [])
        self.assertEqual(kb.raw_read('a', 'not-exist'), [])

    def test_return_all_for_plugin(self):
        i1 = MockInfo()
        i2 = MockInfo()
        i3 = MockInfo()
        
        kb.append('a', 'b', i1)
        kb.append('a', 'b', i2)
        kb.append('a', 'b', i3)
        
        self.assertEqual(kb.get('a', 'b'), [i1, i2, i3])

    def test_append(self):
        i1 = MockInfo()
        i2 = MockInfo()
        i3 = MockInfo()
        
        kb.append('a', 'b', i1)
        kb.append('a', 'b', i1)
        kb.append('a', 'b', i1)
        kb.append('a', 'b', i2)
        kb.append('a', 'b', i3)
        
        self.assertEqual(kb.get('a', 'b'), [i1, i1, i1, i2, i3])

    def test_append_uniq_var_default(self):
        i1 = MockInfo()
        i1.set_uri(URL('http://moth/abc.html?id=1'))
        i1.set_dc(QueryString([('id', ['1'])]))
        i1.set_token(('id', 0))

        i2 = MockInfo()
        i2.set_uri(URL('http://moth/abc.html?id=3'))
        i2.set_dc(QueryString([('id', ['3'])]))
        i2.set_token(('id', 0))

        kb.append_uniq('a', 'b', i1)
        kb.append_uniq('a', 'b', i2)
        self.assertEqual(kb.get('a', 'b'), [i1, ])

    def test_append_uniq_var_specific(self):
        i1 = MockInfo()
        i1.set_uri(URL('http://moth/abc.html?id=1'))
        i1.set_dc(QueryString([('id', ['1'])]))
        i1.set_token(('id', 0))

        i2 = MockInfo()
        i2.set_uri(URL('http://moth/abc.html?id=3'))
        i2.set_dc(QueryString([('id', ['3'])]))
        i2.set_token(('id', 0))

        kb.append_uniq('a', 'b', i1, filter_by='VAR')
        kb.append_uniq('a', 'b', i2, filter_by='VAR')
        self.assertEqual(kb.get('a', 'b'), [i1, ])

    def test_append_uniq_var_bug_10Dec2012(self):
        i1 = MockInfo()
        i1.set_uri(URL('http://moth/abc.html?id=1'))
        i1.set_dc(QueryString([('id', ['1'])]))
        i1.set_token(('id', 0))

        i2 = MockInfo()
        i2.set_uri(URL('http://moth/abc.html?id=1'))
        i2.set_dc(QueryString([('id', ['1'])]))
        i2.set_token(('id', 0))

        kb.append_uniq('a', 'b', i1)
        kb.append_uniq('a', 'b', i2)
        self.assertEqual(kb.get('a', 'b'), [i1, ])
        
    def test_append_uniq_var_not_uniq_diff_url(self):
        i1 = MockInfo()
        i1.set_uri(URL('http://moth/abc.html?id=1'))
        i1.set_dc(QueryString([('id', ['1'])]))
        i1.set_token(('id', 0))

        i2 = MockInfo()
        i2.set_uri(URL('http://moth/def.html?id=3'))
        i2.set_dc(QueryString([('id', ['3'])]))
        i2.set_token(('id', 0))

        kb.append_uniq('a', 'b', i1)
        kb.append_uniq('a', 'b', i2)
        self.assertEqual(kb.get('a', 'b'), [i1, i2])

    def test_append_uniq_var_not_uniq_diff_token_name(self):
        i1 = MockInfo()
        i1.set_uri(URL('http://moth/abc.html?id=1&foo=bar'))
        i1.set_dc(QueryString([('id', ['1']),
                               ('foo', ['bar'])]))
        i1.set_token(('id', 0))

        i2 = MockInfo()
        i2.set_uri(URL('http://moth/abc.html?id=1&foo=bar'))
        i2.set_dc(QueryString([('id', ['3']),
                               ('foo', ['bar'])]))
        i2.set_token(('foo', 0))

        kb.append_uniq('a', 'b', i1)
        kb.append_uniq('a', 'b', i2)
        self.assertEqual(kb.get('a', 'b'), [i1, i2])

    def test_append_uniq_var_not_uniq_diff_token_name_three(self):
        i1 = MockInfo()
        i1.set_uri(URL('http://moth/abc.html?id=1&foo=bar'))
        i1.set_dc(QueryString([('id', ['1']),
                               ('foo', ['bar'])]))
        i1.set_token(('id', 0))

        i2 = MockInfo()
        i2.set_uri(URL('http://moth/abc.html?id=1&foo=bar'))
        i2.set_dc(QueryString([('id', ['3']),
                               ('foo', ['bar'])]))
        i2.set_token(('foo', 0))

        # This instance duplicates i2
        i3 = MockInfo()
        i3.set_uri(URL('http://moth/abc.html?id=1&foo=bar'))
        i3.set_dc(QueryString([('id', ['3']),
                               ('foo', ['bar'])]))
        i3.set_token(('foo', 0))

        kb.append_uniq('a', 'b', i1)
        kb.append_uniq('a', 'b', i2)
        kb.append_uniq('a', 'b', i3)
        self.assertEqual(kb.get('a', 'b'), [i1, i2])

    def test_append_uniq_var_diff_params(self):
        i1 = MockInfo()
        i1.set_uri(URL('http://moth/abc.html?id=1'))
        i1.set_dc(QueryString([('id', ['1'])]))
        i1.set_token(('id', 0))

        i2 = MockInfo()
        i2.set_uri(URL('http://moth/abc.html?id=3&foo=bar'))
        i2.set_dc(QueryString([('id', ['3']), ('foo', ['bar'])]))
        i2.set_token(('id', 0))

        kb.append_uniq('a', 'b', i1)
        kb.append_uniq('a', 'b', i2)
        self.assertEqual(kb.get('a', 'b'), [i1])

    def test_append_uniq_url_uniq(self):
        i1 = MockInfo()
        i1.set_uri(URL('http://moth/abc.html?id=1'))
        i1.set_dc(QueryString([('id', ['1'])]))
        i1.set_token(('id', 0))

        i2 = MockInfo()
        i2.set_uri(URL('http://moth/abc.html?id=3'))
        i2.set_dc(QueryString([('id', ['3'])]))
        i2.set_token(('id', 0))

        kb.append_uniq('a', 'b', i1, filter_by='URL')
        kb.append_uniq('a', 'b', i2, filter_by='URL')
        self.assertEqual(kb.get('a', 'b'), [i1])

    def test_append_uniq_url_different(self):
        i1 = MockInfo()
        i1.set_uri(URL('http://moth/abc.html?id=1'))
        i1.set_dc(QueryString([('id', ['1'])]))
        i1.set_token(('id', 0))

        i2 = MockInfo()
        i2.set_uri(URL('http://moth/def.html?id=3'))
        i2.set_dc(QueryString([('id', ['3'])]))
        i2.set_token(('id', 0))

        kb.append_uniq('a', 'b', i1, filter_by='URL')
        kb.append_uniq('a', 'b', i2, filter_by='URL')
        self.assertEqual(kb.get('a', 'b'), [i1, i2])
        
    def test_append_save(self):
        i1 = MockInfo()
        
        kb.append('a', 'b', i1)
        kb.raw_write('a', 'b', 3)
        
        self.assertEqual(kb.raw_read('a', 'b'), 3)

    def test_save_append(self):
        """
        Although calling raw_write and then append is highly discouraged,
        someone would want to use it.
        """
        i0 = MockInfo()
        self.assertRaises(TypeError, kb.raw_write, 'a', 'b', i0)
        
        i1 = MockInfo()
        i2 = MockInfo()
        kb.append('a', 'b', i1)
        kb.append('a', 'b', i2)
        
        self.assertEqual(kb.get('a', 'b'), [i1, i2])

    def test_all_of_klass(self):
        kb.raw_write('a', 'b', 1)
        self.assertEqual(kb.get_all_entries_of_class(int), [1])

    def test_all_of_klass_str(self):
        kb.raw_write('a', 'b', 'abc')
        self.assertEqual(kb.get_all_entries_of_class(str), ['abc'])

    def test_get_all_uniq_ids_iter(self):
        i1 = MockInfo()
        kb.append('a', 'b', i1)

        uniq_ids = [u for u in kb.get_all_uniq_ids_iter()]

        self.assertEqual(uniq_ids, [i1.get_uniq_id()])

    def test_get_all_uniq_ids_iter_include_ids(self):
        i1 = MockInfo()
        kb.append('a', 'b', i1)

        uniq_ids = [u for u in kb.get_all_uniq_ids_iter(include_ids=[i1.get_uniq_id()])]

        self.assertEqual(uniq_ids, [i1.get_uniq_id()])

    def test_get_all_uniq_ids_iter_include_ids_false(self):
        i1 = MockInfo()
        kb.append('a', 'b', i1)

        uniq_ids = [u for u in kb.get_all_uniq_ids_iter(include_ids=[str(uuid.uuid4())])]

        self.assertEqual(uniq_ids, [])

    def test_all_of_info_vuln(self):
        i1 = MockInfo()
        i2 = MockInfo()

        v1 = MockVuln()
        v2 = MockVuln()

        iset = InfoSet([i2])
        vset = InfoSet([v2])

        kb.append('a', 'b', i1)
        kb.append('w', 'z', iset)
        kb.append('x', 'y', v1)
        kb.append('4', '2', vset)

        self.assertEqual(kb.get_all_vulns(), [v1, vset])
        self.assertEqual(kb.get_all_infos(), [i1, iset])
        self.assertEqual(kb.get_all_findings(), [i1, iset, v1, vset])

    def test_all_of_info_exclude_ids(self):
        i1 = MockInfo()
        i2 = MockInfo()

        v1 = MockVuln()
        v2 = MockVuln()

        iset = InfoSet([i2])
        vset = InfoSet([v2])

        kb.append('a', 'b', i1)
        kb.append('w', 'z', iset)
        kb.append('x', 'y', v1)
        kb.append('4', '2', vset)

        all_findings = kb.get_all_findings()
        all_findings_except_v1 = kb.get_all_findings(exclude_ids=(v1.get_uniq_id(),))
        all_findings_except_v1_v2 = kb.get_all_findings(exclude_ids=(v1.get_uniq_id(), vset.get_uniq_id()))

        self.assertEqual(all_findings, [i1, iset, v1, vset])
        self.assertEqual(all_findings_except_v1, [i1, iset, vset])
        self.assertEqual(all_findings_except_v1_v2, [i1, iset])

    def test_dump_empty(self):
        empty = kb.dump()
        self.assertEqual(empty, {})

    def test_dump(self):
        kb.raw_write('a', 'b', 1)
        self.assertEqual(kb.dump(), {'a': {'b': [1]}})

    def test_clear(self):
        kb.raw_write('a', 'b', 'abc')
        kb.raw_write('a', 'c', 'abc')
        kb.clear('a', 'b')
        self.assertEqual(kb.raw_read('a', 'b'), [])
        self.assertEqual(kb.raw_read('a', 'c'), 'abc')

    def test_overwrite(self):
        kb.raw_write('a', 'b', 'abc')
        kb.raw_write('a', 'b', 'def')
        self.assertEqual(kb.raw_read('a', 'b'), 'def')

    def test_raw_write_dict(self):
        kb.raw_write('a', 'b', {})
        self.assertEqual(kb.raw_read('a', 'b'), {})

    def test_drop_table(self):
        kb = DBKnowledgeBase()
        kb.setup()
        table_name = kb.table_name
        
        db = get_default_persistent_db_instance()
        
        self.assertTrue(db.table_exists(table_name))
        
        kb.remove()
        
        self.assertFalse(db.table_exists(table_name))

    def test_observer_append(self):
        observer1 = Mock()
        info = MockInfo()

        kb.add_observer(observer1)
        kb.append('a', 'b', info)

        observer1.append.assert_called_once_with('a', 'b', info,
                                                 ignore_type=False)

    def test_observer_update(self):
        observer1 = Mock()
        info = MockInfo()

        kb.add_observer(observer1)
        kb.append('a', 'b', info)
        old_info = copy.deepcopy(info)
        info.set_name('new name')
        kb.update(old_info, info)

        observer1.update.assert_called_once_with(old_info, info)

    def test_observer_add_url(self):
        observer1 = Mock()
        url = URL('http://www.w3af.org/')

        kb.add_observer(observer1)
        kb.add_url(url)

        observer1.add_url.assert_called_once_with(url)

    def test_observer_multiple_observers(self):
        observer1 = Mock()
        observer2 = Mock()
        
        kb.add_observer(observer1)
        kb.add_observer(observer2)
        kb.raw_write('a', 'b', 1)

        observer1.append.assert_called_once_with('a', 'b', 1, ignore_type=True)
        observer2.append.assert_called_once_with('a', 'b', 1, ignore_type=True)
        
    def test_pickleable_info(self):
        original_info = MockInfo()
        
        kb.append('a', 'b', original_info)
        unpickled_info = kb.get('a', 'b')[0]
        
        self.assertEqual(original_info, unpickled_info)

    def test_pickleable_vuln(self):
        original_vuln = MockVuln()
        
        kb.append('a', 'b', original_vuln)
        unpickled_vuln = kb.get('a', 'b')[0]
        
        self.assertEqual(original_vuln, unpickled_vuln)
        
    def test_pickleable_shells(self):
        pool = Pool(1)
        xurllib = ExtendedUrllib()
        
        original_shell = Shell(MockVuln(), xurllib, pool)
        
        kb.append('a', 'b', original_shell)
        unpickled_shell = kb.get('a', 'b')[0]
        
        self.assertEqual(original_shell, unpickled_shell)
        self.assertEqual(unpickled_shell.worker_pool, None)
        self.assertEqual(unpickled_shell._uri_opener, None)
        
        pool.terminate()
        pool.join()
        xurllib.end()
        
    def test_pickleable_shells_get_all(self):
        class FakeCore(object):
            worker_pool = Pool(1)
            uri_opener = ExtendedUrllib()
        
        core = FakeCore()
        original_shell = Shell(MockVuln(), core.uri_opener, core.worker_pool)
        
        kb.append('a', 'b', original_shell)
        unpickled_shell = list(kb.get_all_shells(core))[0]
        
        self.assertEqual(original_shell, unpickled_shell)
        self.assertEqual(unpickled_shell.worker_pool, core.worker_pool)
        self.assertEqual(unpickled_shell._uri_opener, core.uri_opener)
        
        core.worker_pool.terminate()
        core.worker_pool.join()
        core.uri_opener.end()
    
    def test_get_by_uniq_id(self):
        i1 = MockInfo()
        kb.append('a', 'b', i1)

        i1_copy = kb.get_by_uniq_id(i1.get_uniq_id())
        self.assertEqual(i1_copy, i1)
    
    def test_get_by_uniq_id_not_exists(self):
        self.assertIs(kb.get_by_uniq_id(hash('foo')), None)
        
    def test_get_by_uniq_id_duplicated_ignores_second(self):
        """
        TODO: Analyze this case, i1 and i2 have both the same ID because they
              have all the same information (this is very very uncommon in a
              real w3af run).
              
              Note that in the get_by_uniq_id call i2 is not returned.
        """
        i1 = MockInfo()
        i2 = MockInfo()
        kb.append('a', 'b', i1)
        kb.append('a', 'b', i2)
        
        i1_copy = kb.get_by_uniq_id(i1.get_uniq_id())
        self.assertEqual(i1_copy, i1)
    
    def test_raw_write_list(self):
        """
        Test for _get_uniq_id which needs to be able to hash any object type.
        """
        kb.raw_write('a', 'b', [1, 2, 3])
        self.assertEqual(kb.raw_read('a', 'b'), [1, 2, 3])
    
    def test_kb_list_shells_empty(self):
        self.assertEqual(kb.get_all_shells(), [])

    def test_kb_list_shells_sqlmap_2181(self):
        """
        Also very related with test_pickleable_shells
        :see: https://github.com/andresriancho/w3af/issues/2181
        """
        w3af_core = w3afCore()
        target = Target(URL('http://w3af.org/'))
        sqlmap_wrapper = SQLMapWrapper(target, w3af_core.uri_opener)

        sqlmap_shell = SQLMapShell(MockVuln(), w3af_core.uri_opener,
                                   w3af_core.worker_pool, sqlmap_wrapper)
        kb.append('a', 'b', sqlmap_shell)

        shells = kb.get_all_shells(w3af_core=w3af_core)
        self.assertEqual(len(shells), 1)
        unpickled_shell = shells[0]

        self.assertEqual(sqlmap_shell, unpickled_shell)
        self.assertIs(unpickled_shell._uri_opener, w3af_core.uri_opener)
        self.assertIs(unpickled_shell.worker_pool, w3af_core.worker_pool)
        self.assertIs(unpickled_shell.sqlmap.proxy._uri_opener,
                      w3af_core.uri_opener)

        w3af_core.quit()

    def test_kb_list_shells_dav_2181(self):
        """
        :see: https://github.com/andresriancho/w3af/issues/2181
        """
        w3af_core = w3afCore()
        exploit_url = URL('http://w3af.org/')

        shell = DAVShell(MockVuln(), w3af_core.uri_opener,
                         w3af_core.worker_pool, exploit_url)
        kb.append('a', 'b', shell)

        shells = kb.get_all_shells(w3af_core=w3af_core)
        self.assertEqual(len(shells), 1)
        unpickled_shell = shells[0]

        self.assertEqual(shell, unpickled_shell)
        self.assertIs(unpickled_shell._uri_opener, w3af_core.uri_opener)
        self.assertIs(unpickled_shell.worker_pool, w3af_core.worker_pool)
        self.assertEqual(unpickled_shell.exploit_url, shell.exploit_url)

        w3af_core.quit()

    def test_kb_list_shells_eval_2181(self):
        """
        :see: https://github.com/andresriancho/w3af/issues/2181
        """
        w3af_core = w3afCore()

        shellcodes = get_shell_code('php', 'ls')
        shellcode_generator = shellcodes[0][2]

        shell = EvalShell(MockVuln(), w3af_core.uri_opener,
                          w3af_core.worker_pool, shellcode_generator)
        kb.append('a', 'b', shell)

        shells = kb.get_all_shells(w3af_core=w3af_core)
        self.assertEqual(len(shells), 1)
        unpickled_shell = shells[0]

        self.assertEqual(shell, unpickled_shell)
        self.assertIs(unpickled_shell._uri_opener, w3af_core.uri_opener)
        self.assertIs(unpickled_shell.worker_pool, w3af_core.worker_pool)
        self.assertEqual(unpickled_shell.shellcode_generator.args,
                         shell.shellcode_generator.args)

        w3af_core.quit()

    def test_kb_list_shells_file_upload_2181(self):
        """
        :see: https://github.com/andresriancho/w3af/issues/2181
        """
        w3af_core = w3afCore()
        exploit_url = URL('http://w3af.org/')

        shell = FileUploadShell(MockVuln(), w3af_core.uri_opener,
                                w3af_core.worker_pool, exploit_url)
        kb.append('a', 'b', shell)

        shells = kb.get_all_shells(w3af_core=w3af_core)
        self.assertEqual(len(shells), 1)
        unpickled_shell = shells[0]

        self.assertEqual(shell, unpickled_shell)
        self.assertIs(unpickled_shell._uri_opener, w3af_core.uri_opener)
        self.assertIs(unpickled_shell.worker_pool, w3af_core.worker_pool)
        self.assertEqual(unpickled_shell._exploit_url, shell._exploit_url)

        w3af_core.quit()

    def test_kb_list_shells_file_read_2181(self):
        """
        :see: https://github.com/andresriancho/w3af/issues/2181
        """
        w3af_core = w3afCore()
        header_len, footer_len = 1, 1

        vuln = MockVuln()

        shell = FileReaderShell(vuln, w3af_core.uri_opener,
                                w3af_core.worker_pool, header_len, footer_len)
        kb.append('a', 'b', shell)

        shells = kb.get_all_shells(w3af_core=w3af_core)
        self.assertEqual(len(shells), 1)
        unpickled_shell = shells[0]

        self.assertEqual(shell, unpickled_shell)
        self.assertIs(unpickled_shell._uri_opener, w3af_core.uri_opener)
        self.assertIs(unpickled_shell.worker_pool, w3af_core.worker_pool)
        self.assertEqual(unpickled_shell._header_length, shell._header_length)
        self.assertEqual(unpickled_shell._footer_length, shell._footer_length)

        w3af_core.quit()

    def test_kb_list_shells_os_commanding_2181(self):
        """
        :see: https://github.com/andresriancho/w3af/issues/2181
        """
        w3af_core = w3afCore()

        vuln = MockVuln()
        vuln['separator'] = '&'
        vuln['os'] = 'linux'
        strategy = BasicExploitStrategy(vuln)
        shell = OSCommandingShell(strategy, w3af_core.uri_opener,
                                  w3af_core.worker_pool)
        kb.append('a', 'b', shell)

        shells = kb.get_all_shells(w3af_core=w3af_core)
        self.assertEqual(len(shells), 1)
        unpickled_shell = shells[0]

        self.assertEqual(shell, unpickled_shell)
        self.assertIs(unpickled_shell._uri_opener, w3af_core.uri_opener)
        self.assertIs(unpickled_shell.worker_pool, w3af_core.worker_pool)
        self.assertEqual(unpickled_shell.strategy.vuln, vuln)

        w3af_core.quit()

    def test_kb_list_shells_rfi_2181(self):
        """
        :see: https://github.com/andresriancho/w3af/issues/2181
        """
        w3af_core = w3afCore()

        vuln = MockVuln()
        url = URL('http://moth/?a=1')
        freq = FuzzableRequest(url)
        exploit_mutant = QSMutant.create_mutants(freq, [''], [], False, {})[0]

        shell = RFIShell(vuln, w3af_core.uri_opener, w3af_core.worker_pool,
                         exploit_mutant)
        kb.append('a', 'b', shell)

        shells = kb.get_all_shells(w3af_core=w3af_core)
        self.assertEqual(len(shells), 1)
        unpickled_shell = shells[0]

        self.assertEqual(shell, unpickled_shell)
        self.assertIs(unpickled_shell._uri_opener, w3af_core.uri_opener)
        self.assertIs(unpickled_shell.worker_pool, w3af_core.worker_pool)
        self.assertEqual(unpickled_shell._exploit_mutant, exploit_mutant)

        w3af_core.quit()

    def test_kb_list_shells_rfi_port_scan_2181(self):
        """
        :see: https://github.com/andresriancho/w3af/issues/2181
        """
        w3af_core = w3afCore()

        vuln = MockVuln()
        url = URL('http://moth/?a=1')
        freq = FuzzableRequest(url)
        exploit_mutant = QSMutant.create_mutants(freq, [''], [], False, {})[0]

        shell = PortScanShell(vuln, w3af_core.uri_opener, w3af_core.worker_pool,
                              exploit_mutant)
        kb.append('a', 'b', shell)

        shells = kb.get_all_shells(w3af_core=w3af_core)
        self.assertEqual(len(shells), 1)
        unpickled_shell = shells[0]

        self.assertEqual(shell, unpickled_shell)
        self.assertIs(unpickled_shell._uri_opener, w3af_core.uri_opener)
        self.assertIs(unpickled_shell.worker_pool, w3af_core.worker_pool)
        self.assertEqual(unpickled_shell._exploit_mutant, exploit_mutant)

        w3af_core.quit()

    def test_kb_list_shells_xpath_2181(self):
        """
        :see: https://github.com/andresriancho/w3af/issues/2181
        """
        w3af_core = w3afCore()
        vuln = MockVuln()

        str_delim = '&'
        true_cond = ''
        use_difflib = False
        is_error_response = IsErrorResponse(vuln, w3af_core.uri_opener,
                                            use_difflib)

        shell = XPathReader(vuln, w3af_core.uri_opener,
                            w3af_core.worker_pool, str_delim, true_cond,
                            is_error_response)
        kb.append('a', 'b', shell)

        shells = kb.get_all_shells(w3af_core=w3af_core)
        self.assertEqual(len(shells), 1)
        unpickled_shell = shells[0]

        self.assertEqual(shell, unpickled_shell)
        self.assertIs(unpickled_shell._uri_opener, w3af_core.uri_opener)
        self.assertIs(unpickled_shell.worker_pool, w3af_core.worker_pool)
        self.assertEqual(unpickled_shell.STR_DELIM, shell.STR_DELIM)
        self.assertEqual(unpickled_shell.TRUE_COND, shell.TRUE_COND)
        self.assertEqual(unpickled_shell.is_error_resp.use_difflib, use_difflib)
        self.assertEqual(unpickled_shell.is_error_resp.url_opener,
                         w3af_core.uri_opener)

        w3af_core.quit()

    def test_update_info(self):
        info = MockInfo()
        kb.append('a', 'b', info)
        update_info = copy.deepcopy(info)
        update_info.set_name('a')
        update_uniq_id = update_info.get_uniq_id()
        kb.update(info, update_info)

        self.assertNotEqual(update_info, info)
        self.assertEqual(update_info, kb.get_by_uniq_id(update_uniq_id))

    def test_update_vuln(self):
        vuln = MockVuln()
        kb.append('a', 'b', vuln)
        update_vuln = copy.deepcopy(vuln)
        update_vuln.set_name('a')
        update_uniq_id = update_vuln.get_uniq_id()
        kb.update(vuln, update_vuln)

        self.assertNotEqual(update_vuln, vuln)
        self.assertEqual(update_vuln, kb.get_by_uniq_id(update_uniq_id))

    def test_update_exception(self):
        vuln = MockVuln()
        kb.append('a', 'b', vuln)
        original_id = vuln.get_uniq_id()

        # Cause error by changing vuln uniq_id
        update_vuln = vuln
        update_vuln._uniq_id = str(uuid.uuid4())
        modified_id = vuln.get_uniq_id()

        self.assertNotEqual(original_id, modified_id)
        self.assertRaises(DBException, kb.update, vuln, update_vuln)

    def test_get_one(self):
        vuln = MockVuln()
        kb.append('a', 'b', vuln)
        kb_vuln = kb.get_one('a', 'b')

        #pylint: disable=E1103
        self.assertEqual(kb_vuln.get_uniq_id(), vuln.get_uniq_id())
        self.assertEqual(kb_vuln, vuln)
        #pylint: enable=E1103

    def test_get_one_none_found(self):
        empty_list = kb.get_one('a', 'b')
        self.assertEqual(empty_list, [])

    def test_get_one_more_than_one_found(self):
        vuln = MockVuln()
        kb.append('a', 'b', vuln)
        kb.append('a', 'b', vuln)
        self.assertRaises(RuntimeError, kb.get_one, 'a', 'b')

    def test_append_uniq_group_empty_address(self):
        vuln = MockVuln()
        info_set, created = kb.append_uniq_group('a', 'b', vuln)

        self.assertIsInstance(info_set, InfoSet)
        self.assertTrue(created)
        self.assertEqual(info_set.get_urls(), [vuln.get_url()])
        self.assertEqual(info_set.get_name(), vuln.get_name())
        self.assertEqual(info_set.get_id(), vuln.get_id())
        self.assertEqual(info_set.get_plugin_name(), vuln.get_plugin_name())

    def test_append_uniq_group_match_filter_func(self):
        vuln = MockVuln()
        kb.append_uniq_group('a', 'b', vuln, group_klass=MockInfoSetTrue)
        info_set, created = kb.append_uniq_group('a', 'b', vuln,
                                                 group_klass=MockInfoSetTrue)

        self.assertFalse(created)
        self.assertIsInstance(info_set, InfoSet)
        self.assertEqual(len(info_set.infos), 2)

    def test_multiple_append_uniq_group(self):
        def multi_append():
            for i in xrange(InfoSet.MAX_INFO_INSTANCES * 2):
                vuln = MockVuln()
                kb.append_uniq_group('a', 'b', vuln, group_klass=MockInfoSetTrue)

            info_set_list = kb.get('a', 'b')

            self.assertEqual(len(info_set_list), 1)

            info_set = info_set_list[0]
            self.assertEqual(len(info_set.infos), InfoSet.MAX_INFO_INSTANCES)
            return True

        pool = Pool(2)

        r1 = pool.apply_async(multi_append)
        r2 = pool.apply_async(multi_append)
        r3 = pool.apply_async(multi_append)

        self.assertTrue(r1.get())
        self.assertTrue(r2.get())
        self.assertTrue(r3.get())

        pool.terminate()
        pool.join()

    def test_info_set_keep_uniq_id(self):
        #
        # Create a new InfoSet, load it from the KB, confirm that it has
        # the same uniq_id
        #
        vuln = MockVuln(name='Foos')

        info_set_a, created = kb.append_uniq_group('a', 'b', vuln,
                                                   group_klass=MockInfoSetNames)

        self.assertTrue(created)

        info_set_b = kb.get('a', 'b')[0]

        self.assertEqual(info_set_a.get_uniq_id(),
                         info_set_b.get_uniq_id())

        #
        # Change the InfoSet a little bit by adding a new Info. That should
        # change the uniq_id
        #
        vuln = MockVuln(name='Foos')
        _, created = kb.append_uniq_group('a', 'b', vuln,
                                          group_klass=MockInfoSetNames)

        self.assertFalse(created)

        info_set_b = kb.get('a', 'b')[0]

        self.assertNotEqual(info_set_a.get_uniq_id(),
                            info_set_b.get_uniq_id())

    def test_info_set_keep_uniq_id_after_max_info_instances(self):
        #
        # Create one InfoSet, add MAX_INFO_INSTANCES, assert that the ID is not
        # changed afterwards
        #
        vuln = MockVuln(name='Foos')

        for _ in xrange(MockInfoSetNames.MAX_INFO_INSTANCES + 1):
            kb.append_uniq_group('a', 'b', vuln, group_klass=MockInfoSetNames)

        info_set_before = kb.get('a', 'b')[0]

        # Now some rounds of testing
        for _ in xrange(5):
            info_set_after, _ = kb.append_uniq_group('a', 'b', vuln,
                                                     group_klass=MockInfoSetNames)

            self.assertEqual(info_set_before.get_uniq_id(),
                             info_set_after.get_uniq_id())

    def test_append_uniq_group_no_match_filter_func(self):
        vuln1 = MockVuln(name='Foos')
        vuln2 = MockVuln(name='Bars')
        kb.append_uniq_group('a', 'b', vuln1, group_klass=MockInfoSetFalse)
        info_set, created = kb.append_uniq_group('a', 'b', vuln2,
                                                 group_klass=MockInfoSetFalse)

        self.assertIsInstance(info_set, InfoSet)
        self.assertTrue(created)
        self.assertEqual(len(info_set.infos), 1)

        raw_data = kb.get('a', 'b')
        self.assertEqual(len(raw_data), 2)
        self.assertIsInstance(raw_data[0], InfoSet)
        self.assertIsInstance(raw_data[1], InfoSet)

        self.assertEqual(raw_data[0].first_info.get_name(), 'Foos')
        self.assertEqual(raw_data[1].first_info.get_name(), 'Bars')

    def test_append_uniq_group_filter_func_specific(self):
        vuln1 = MockVuln(name='Foos')
        vuln2 = MockVuln(name='Bars')
        vuln3 = MockVuln(name='Foos', _id=42)
        kb.append_uniq_group('a', 'b', vuln1, group_klass=MockInfoSetNames)
        kb.append_uniq_group('a', 'b', vuln2, group_klass=MockInfoSetNames)
        kb.append_uniq_group('a', 'b', vuln3, group_klass=MockInfoSetNames)

        raw_data = kb.get('a', 'b')
        self.assertEqual(len(raw_data), 2)
        self.assertIsInstance(raw_data[0], InfoSet)
        self.assertIsInstance(raw_data[1], InfoSet)

        self.assertEqual(raw_data[0].get_name(), 'Foos')
        self.assertEqual(len(raw_data[0].infos), 2)
        self.assertEqual(raw_data[0].infos[1].get_id(), [42])
        self.assertEqual(raw_data[1].first_info.get_name(), 'Bars')

    def test_append_uniq_group_filter_func_attribute_match(self):
        vuln1 = MockVuln(name='Foos', _id=47)
        vuln1['tag'] = 'foo'

        vuln2 = MockVuln(name='Bars')
        vuln2['tag'] = 'bar'

        vuln3 = MockVuln(name='Foos', _id=42)
        vuln3['tag'] = 'foo'

        kb.append_uniq_group('a', 'b', vuln1, group_klass=MockInfoSetITag)
        kb.append_uniq_group('a', 'b', vuln2, group_klass=MockInfoSetITag)
        kb.append_uniq_group('a', 'b', vuln3, group_klass=MockInfoSetITag)

        raw_data = kb.get('a', 'b')
        self.assertEqual(len(raw_data), 2)
        self.assertIsInstance(raw_data[0], InfoSet)
        self.assertIsInstance(raw_data[1], InfoSet)

        self.assertEqual(raw_data[0].get_name(), 'Foos')
        self.assertEqual(len(raw_data[0].infos), 2)
        self.assertEqual(raw_data[0].infos[1].get_id(), [42])
        self.assertEqual(raw_data[0].infos[0].get_id(), [47])
        self.assertEqual(raw_data[1].first_info.get_name(), 'Bars')


class MockInfoSetITag(InfoSet):
    ITAG = 'tag'


class MockInfoSetNames(InfoSet):
    def match(self, info):
        return info.get_name() == self.get_name()


class MockInfoSetFalse(InfoSet):
    def match(self, info):
        return False


class MockInfoSetTrue(InfoSet):
    def match(self, info):
        return True
