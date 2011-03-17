'''
test_sca.py

Copyright 2011 Andres Riancho

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

from pymock import PyMockTestCase

from ..sca import PhpSCA, Scope, CodeSyntaxError

class TestPHPSCA(PyMockTestCase):
    '''
    Test unit for PHP Static Code Analyzer
    '''
    
    def setUp(self):
        PyMockTestCase.setUp(self)

    def test_vars(self):
        code = '''
            <?
              $foo = $_GET['bar'];
              $spam = $_POST['blah'];
              $eggs = 'blah' . 'blah';
              if ($eggs){
                  $xx = 'waka-waka';
                  $yy = $foo;
              }
            ?>
            '''
        analyzer = PhpSCA(code)
        # Get all vars
        vars = analyzer.get_vars(usr_controlled=False)
        self.assertEquals(5, len(vars))
        # Get user controlled vars
        usr_cont_vars = analyzer.get_vars(usr_controlled=True)
        self.assertEquals(3, len(usr_cont_vars))
        # Test $foo
        foovar = usr_cont_vars[0]
        self.assertEquals('$foo', foovar.name)
        self.assertTrue(foovar.controlled_by_user)
        self.assertFalse(foovar.is_root)
        self.assertTrue(foovar.parent)
        # Test $spam
        spamvar = usr_cont_vars[1]
        self.assertEquals('$spam', spamvar.name)
        # Test $spam
        yyvar = usr_cont_vars[2]
        self.assertEquals('$yy', yyvar.name)
    
    def test_override_var(self):
        code = '''
        <?php
            $var1 = $_GET['param'];
            $var1 = 'blah';
            $var2 = escapeshellarg($_GET['param2']);
            $var3 = 'blah';
            if ($x){
                $var3 = $_POST['param2'];
            }
            else{
                $var3 = 'blah'.'blah'; 
            }
        ?>
        '''
        analyzer = PhpSCA(code)
        vars = analyzer.get_vars(usr_controlled=False)
        
        # 'var1' is safe
        var1 = vars[0]
        self.assertFalse(var1.controlled_by_user)

        # 'var2' is controlled by the user but is safe for OS-Commanding
        var2 = vars[1]
        self.assertTrue(var2.controlled_by_user)
        self.assertFalse(var2.is_tainted_for('OS_COMMANDING'))
        
        # 'var3' must still be controllable by user
        var3 = vars[2]
        self.assertTrue(var3.controlled_by_user)
    
    def test_vars_lineno(self):
        pass
    
    def test_vars_dependencies(self):
        code = '''
        <?
          $x1 = 'waca-waka';
          $x2 = '#!~?#*' + $x1;
          $x3 = func($x2);
          $y = $_COOKIES['1'];
          $y2 = 'ls ' . $y;
          $z = $x2 + $x3;
        ?>
        '''
        analyzer = PhpSCA(code)
        vars = analyzer.get_vars(usr_controlled=False)
        vars.sort(cmp=lambda x, y: cmp(x.lineno, y.lineno))
        x1deps, x2deps, x3deps, ydeps, y2deps, zdeps = \
                            [[vd.name for vd in v.deps()] for v in vars]

        self.assertEquals([], x1deps)
        self.assertEquals(['$x1'], x2deps)
        self.assertEquals(['$x2', '$x1'], x3deps)
        self.assertEquals(['$_COOKIES'], ydeps)
        self.assertEquals(['$y', '$_COOKIES'], y2deps)
        self.assertEquals(['$x2', '$x1'], zdeps)
    
    def test_var_comp_operators(self):
        code = '''
        <?php
            $var0 = 'bleh';
            $var1 = $_GET['param'];
            $var2 = 'blah';
        ?>
        '''
        analyzer = PhpSCA(code)
        vars = analyzer.get_vars(usr_controlled=False)
        
        code2 = '''
        <?php
            $var0 = 'bleh';
            
            $var1 = 'blah';
            if ($x){
                $var2 = $_POST['param2'];
            }
            else{
                $var2 = 'blah'.'blah'; 
            }
        ?>
        '''
        analyzer = PhpSCA(code2)
        vars2 = analyzer.get_vars(usr_controlled=False)
        
        c1_var0 = vars[0]
        c2_var0 = vars2[0]
        c1_var0._scope = c2_var0._scope
        self.assertTrue(c2_var0 == c1_var0)
        
        c1_var1 = vars[1]
        c2_var1 = vars2[1]
        c2_var1._scope = c1_var1._scope
        self.assertTrue(c2_var1 > c1_var1)
        
        c1_var2 = vars[2]
        c2_var2 = vars2[2]
        self.assertTrue(c2_var2 > c1_var2)
    
    def test_vuln_func_get_sources_1(self):
        code = '''
        <?
            $eggs = $_GET['bar'];
            $foo = func($eggs);
            $a = 'ls ' . $foo; 
            exec($a);
        ?>
        '''
        analyzer = PhpSCA(code)
        execfunc = analyzer.get_func_calls(vuln=True)[0]
        self.assertTrue(
            len(execfunc.vulnsources) == 1 and 'bar' in execfunc.vulnsources)
    
    def test_vuln_func_get_sources_2(self):
        code = '''<? echo file_get_contents($_REQUEST['file']); ?>'''
        analyzer = PhpSCA(code)
        execfunc = analyzer.get_func_calls(vuln=True)[0]
        self.assertTrue(
            len(execfunc.vulnsources) == 1 and 'file' in execfunc.vulnsources)
    
    def test_vuln_func_get_sources_3(self):
        code = '''<? system($_GET['foo']); ?>'''
        analyzer = PhpSCA(code)
        execfunc = analyzer.get_func_calls(vuln=True)[0]
        self.assertTrue(
            len(execfunc.vulnsources) == 1 and 'foo' in execfunc.vulnsources)
    
    def test_vuln_functions_1(self):
        code = '''
        <?php
          $var = $_GET['bleh'];
          if ($x){
              $var = 2;
              // not vuln!
              system($var);
          }
          // vuln for OS COMMANDING!
          system($var);
        ?>
        '''
        analyzer = PhpSCA(code)
        sys1, sys2 = analyzer.get_func_calls()
        # First system call
        self.assertEquals(0, len(sys1.vulntypes))
        # Second system call
        self.assertTrue('OS_COMMANDING' in sys2.vulntypes)
    
    def test_vuln_functions_2(self):
        code = '''
        <?
          $foo = $_GET['bar'];
          system('ls ' . $foo);
          echo file_get_contents($foo);
        ?>
        '''
        analyzer = PhpSCA(code)
        syscall, echocall = analyzer.get_func_calls()
        self.assertTrue('OS_COMMANDING' in syscall.vulntypes)
        self.assertTrue('XSS' in echocall.vulntypes)
        #
        # FIXME: THIS IS FAILING. NEEDS TO BE FIXED
        #
        self.assertTrue('FILE_DISCLOSURE' in echocall.vulntypes)
    
    def test_vuln_functions_3(self):
        code = '''
        <?php
          $var1 = escapeshellarg($_GET['param']);
          system($var1);
          system(escapeshellarg($_GET['param']));
          system(myfunc(escapeshellarg($_GET['param'])));
        ?>
        '''
        analyzer = PhpSCA(code)
        syscall1, syscall2, syscall3 = analyzer.get_func_calls()
        # Both must be SAFE!
        self.assertEquals(0, len(syscall1.vulntypes))
        self.assertEquals(0, len(syscall2.vulntypes))
        self.assertEquals(0, len(syscall3.vulntypes))
    
    def test_vuln_functions_4(self):
        code = '''
        <?
        $foo = $_GET['foo'];
        if ( $spam == $eggs ){
             $foo = 'ls';
             system($foo);
        }
        else{
             echo $foo;
             system($foo);
        }
        ?>
        '''
        analyzer = PhpSCA(code)
        sys1, echo, sys2 = analyzer.get_func_calls()
        self.assertEquals([], sys1.vulntypes)
        self.assertTrue('XSS' in echo.vulntypes)
        self.assertTrue('OS_COMMANDING' in sys2.vulntypes)
    
    def test_vuln_functions_5(self):
        code = '''<?
        $foo = 1;
        if ( $spam == $eggs ){
             $foo = $_GET['foo'];
        }
        else{
             $foo = 1;
        }
        include($foo);
        ?>'''
        inccall = PhpSCA(code).get_func_calls()[0]
        self.assertTrue('FILE_INCLUDE' in inccall.vulntypes)
        
    def test_syntax_error(self):
        invalidcode = '''
        <?php
          $var1 == escapeshellarg($_ GET['param']);
        ?>
        '''
        self.assertRaises(CodeSyntaxError, PhpSCA, invalidcode)


class TestScope(PyMockTestCase):
    
    def setUp(self):
        PyMockTestCase.setUp(self)
        self.scope = Scope(None, parent_scope=None)
    
    def test_has_builtin_container(self):
        self.assertEquals(
                    dict, type(getattr(self.scope, '_builtins', None)))
    
    def test_add_var(self):
        self.assertRaises(ValueError, self.scope.add_var, None)
    