'''
Created on Feb 28, 2011

@author: jandalia
'''

from pymock import PyMockTestCase #, method, override, dontcare, set_count

from ..sca import PhpSCA, VariableDef, FuncCall

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
        analyzer.start()
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
        analyzer.start()
        vars = analyzer.get_vars(usr_controlled=False)
        
        # 'var1' is clean
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
    
    def test_var_comp_operators(self):
        code = '''
        <?php
            $var0 = 'bleh';
            $var1 = $_GET['param'];
            $var2 = 'blah';
        ?>
        '''
        analyzer = PhpSCA(code)
        analyzer.start()
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
        analyzer.start()
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
    
    def test_vuln_functions_case_one(self):
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
        analyzer.start()
        funcs = analyzer.get_funcs()
        # First system call
        first_sys = funcs[0]
        self.assertTrue(first_sys.vuln_type == FuncCall.IS_CLEAN)
        # Second system call
        sec_sys = funcs[1]
        self.assertTrue(sec_sys.vuln_type == 'OS_COMMANDING')
    
    def test_vuln_functions_case_two(self):
        code = '''
        <?
            $foo = $_GET['bar'];
            system('ls ' . $foo);
            echo file_get_contents($foo);
        ?>
        '''
        analyzer = PhpSCA(code)
        analyzer.start()
        funcs = analyzer.get_funcs()
        syscall = funcs[0]
        
    
    def test_syntax_error(self):
        pass


class TestScope(PyMockTestCase):
    
    def setUp(self):
        PyMockTestCase.setUp(self)
    
    def test_add_var(self):
#        self.assertRaises(ValueError, scope.add_var, None)
        pass