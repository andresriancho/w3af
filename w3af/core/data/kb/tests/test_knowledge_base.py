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
import unittest

from mock import Mock, call

from w3af.core.controllers.threads.threadpool import Pool
from w3af.core.controllers.exceptions import DBException

from w3af.core.data.parsers.url import URL
from w3af.core.data.kb.knowledge_base import kb, DBKnowledgeBase
from w3af.core.data.kb.tests.test_info import MockInfo
from w3af.core.data.kb.tests.test_vuln import MockVuln
from w3af.core.data.kb.shell import Shell
from w3af.core.data.kb.info import Info
from w3af.core.data.kb.vuln import Vuln 
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
from w3af.plugins.attack.rfi import RFIShell
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
        
    def test_append_uniq_var_not_uniq(self):
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
        self.assertEqual(kb.get('a', 'b'), [i1,])

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
        table_name = kb.table_name
        
        db = get_default_persistent_db_instance()
        
        self.assertTrue(db.table_exists(table_name))
        
        kb.remove()
        
        self.assertFalse(db.table_exists(table_name))

    def test_types_observer(self):
        observer = Mock()
        info_inst = MockInfo()
        
        kb.add_types_observer(Info, observer)
        kb.append('a', 'b', info_inst)
        observer.assert_called_once_with('a', 'b', info_inst)
        observer.reset_mock()
        
        info_inst = MockInfo()
        kb.append('a', 'c', info_inst)
        observer.assert_called_with('a', 'c', info_inst)
        observer.reset_mock()

        # Should NOT call it because it is NOT an Info instance        
        some_int = 3
        kb.raw_write('a', 'd', some_int)
        self.assertEqual(observer.call_count, 0)
        
    def test_observer_all(self):
        observer = Mock()
        
        kb.add_observer(None, None, observer)
        kb.raw_write('a', 'b', 1)
        
        observer.assert_called_once_with('a', 'b', 1)
        observer.reset_mock()
        
        i = MockInfo()
        kb.append('a', 'c', i)
        observer.assert_called_with('a', 'c', i)
        
    def test_observer_location_a(self):
        observer = Mock()
        
        kb.add_observer('a', None, observer)
        kb.raw_write('a', 'b', 1)
        
        observer.assert_called_once_with('a', 'b', 1)
        observer.reset_mock()
        
        # Shouldn't call the observer
        kb.raw_write('xyz', 'b', 1)
        self.assertFalse(observer.called)
        
        i = MockInfo()
        kb.append('a', 'c', i)
        observer.assert_called_with('a', 'c', i)
        
    def test_observer_location_b(self):
        observer = Mock()
        
        kb.add_observer('a', 'b', observer)
        kb.raw_write('a', 'b', 1)
        
        observer.assert_called_once_with('a', 'b', 1)
        observer.reset_mock()
        
        # Shouldn't call the observer
        kb.raw_write('a', 'xyz', 1)
        self.assertFalse(observer.called)
        
        i = MockInfo()
        kb.append('a', 'b', i)
        observer.assert_called_with('a', 'b', i)

    def test_observer_multiple_observers(self):
        observer1 = Mock()
        observer2 = Mock()
        
        kb.add_observer(None, None, observer1)
        kb.add_observer(None, None, observer2)
        kb.raw_write('a', 'b', 1)

        observer1.assert_called_once_with('a', 'b', 1)
        observer2.assert_called_once_with('a', 'b', 1)
        
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
        kb.raw_write('a', 'b', [1,2,3])
        self.assertEqual(kb.raw_read('a','b'), [1,2,3])
    
    def test_url_observer(self):
        observer = Mock()
        kb.add_url_observer(observer)
        
        url = URL('http://w3af.org/')
        kb.add_url(url)
        
        self.assertEqual(observer.call_count, 1)
        self.assertEqual(observer.call_args, call(url,))
        self.assertIs(observer.call_args[0][0], url)

    def test_url_observer_multiple(self):
        observer_1 = Mock()
        observer_2 = Mock()
        kb.add_url_observer(observer_1)
        kb.add_url_observer(observer_2)
        
        url = URL('http://w3af.org/')
        kb.add_url(url)
        
        self.assertEqual(observer_1.call_count, 1)
        self.assertEqual(observer_2.call_count, 1)

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
        update_info = Info.from_info(info)
        update_info.set_name('a')
        update_uniq_id = update_info.get_uniq_id()
        kb.update(info, update_info)

        self.assertNotEqual(update_info, info)
        self.assertEqual(update_info, kb.get_by_uniq_id(update_uniq_id))

    def test_update_vuln(self):
        vuln = MockVuln()
        kb.append('a', 'b', vuln)
        update_vuln = Vuln.from_vuln(vuln)
        update_vuln.set_name('a')
        update_uniq_id = update_vuln.get_uniq_id()
        kb.update(vuln, update_vuln)

        self.assertNotEqual(update_vuln, vuln)
        self.assertEqual(update_vuln, kb.get_by_uniq_id(update_uniq_id))

    def test_update_exception(self):
        vuln = MockVuln()
        kb.append('a', 'b', vuln)
        # Cause error by changing vuln uniq_id
        update_vuln = vuln
        update_vuln.set_name('a')
        self.assertRaises(DBException, kb.update, vuln, update_vuln)
