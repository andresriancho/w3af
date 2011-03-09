'''
Created on Feb 28, 2011

@author: jandalia
'''

from phply import phplex
from phply.phpparse import parser 
import phply.phpast as phpast


# We prefer our way. Slight modification to original 'accept' method.
# Now we can now know which is the parent and siblings of the current
# node while the AST traversal takes place. This will be *super* useful
# for pushing/popping the scopes from the stack. 
Node = phpast.Node

def accept(nodeinst, visitor):
    skip = visitor(nodeinst)    
    if skip:
        return
        
    for field in nodeinst.fields:
        value = getattr(nodeinst, field)
        
        if isinstance(value, Node):
            # Add parent
            value._parent_node = nodeinst
            value.accept(visitor)
        
        elif isinstance(value, list):
            valueset = set(value)
            for item in value:
                if isinstance(item, Node):
                    # Set parent
                    item._parent_node = nodeinst
                    # Set siblings
                    item._siblings = list(set(valueset - set([item])))
                    item.accept(visitor)

# We also want the Nodes to be hashable
def __hash__(nodeinst):
    return hash(nodeinst.lineno)

def is_descendant(nodeinst, onode):
    return not (onode in getattr(nodeinst, '_siblings', []) or \
                onode._parent_node == nodeinst)

# Finally add/monkeypatch our methods to phpast.Node class.
Node.__hash__ = __hash__
Node.is_descendant = is_descendant
Node.accept = accept


class PhpSCA(object):
    '''
    TODO: Docstring here
    '''

    def __init__(self, code, debugmode=False):
        lexer = phplex.lexer.clone()
        self._ast_code = parser.parse(code, lexer=lexer)
        GlobalParentNodeType = phpast.node('GlobalParentNodeType', \
                                           ['name', 'children', '_parent_node'])
        self._global_pnode = GlobalParentNodeType('dummy', self._ast_code, None)
        # Define scope
        scope = Scope(self._global_pnode, parent_scope=None)
        #
        # TODO: NO! Move this vars to a parent scope!!!
        # (it'd be a special *Global* scope!)
        # When this is done change the "set" calculus below
        #
        self._user_vars = [VariableDef(uv, -1, scope) \
                           for uv in VariableDef.USER_VARS]
        map(scope.add_var, self._user_vars)
        self._scopes = [scope]
        # FuncCall nodes
        self._functions = []
        # Debugging purpose
        self.debugmode = False
    
    def start(self):
        '''
        Start AST traversal
        '''
        global_pnode = self._global_pnode
        nodesset = set(self._ast_code)
        
        # Set parent and siblings
        for node in self._ast_code:
            node._siblings = list(nodesset - set([node]))
            node._parent_node = global_pnode
        
        # Start AST traversal!
        global_pnode.accept(self._visitor)
    
    def get_vars(self, usr_controlled=False):
        all_vars = []
        filter_tainted = (lambda v: v.controlled_by_user) if usr_controlled \
                            else (lambda v: 1)
        
        for scope in self._scopes:
            all_vars += filter(filter_tainted, scope.get_all_vars())
            all_vars = list(set(all_vars) - set(self._user_vars))
        
        return all_vars
    
    def get_funcs(self, vuln=False):
        filter_vuln = (lambda f: f.vuln_type != FuncCall.IS_CLEAN) \
                        if vuln else (lambda f: True)
        return filter(filter_vuln, self._functions)
    
    def _visitor(self, node):
        '''
        Visitor method for AST travesal. Used as arg of AST nodes 'accept'
        method (Visitor Design Pattern)
        '''
        currscope = self._scopes[-1]
        
        # Pop scope from stack? If 'node' is not a child it means that 
        # we started analyzing a parent or a sibling => this scope is closed
        if not node.is_descendant(currscope._ast_node):
            self._scopes.pop()
            currscope = self._scopes[-1]
        
        # Create FuncCall nodes. 'echo' and 'print' are PHP special functions
        if type(node) in (phpast.FunctionCall, phpast.Echo, phpast.Print):
            name = getattr(node, 'name', node.__class__.__name__.lower())
            fc = FuncCall(name, node.lineno, node, currscope)
            self._functions.append(fc)
            # Stop parsing children nodes
            return True
        
        # Create the VariableDef
        elif type(node) == phpast.Assignment:
            varnode = node.node
            newvar = VariableDef(varnode.name, varnode.lineno,
                                 currscope, ast_node=node)
            currscope.add_var(newvar)
            # Stop parsing children nodes
            return True
        
        elif type(node) in (phpast.If, phpast.Else, phpast.ElseIf, phpast.While,
                            phpast.DoWhile, phpast.For, phpast.Foreach):
            # Create new Scope and push it onto the stack 
            newscope = Scope(node, parent_scope=currscope)
            self._scopes.append(newscope)
            return False
        
        return False


class NodeRep(object):
    '''
    Abstract Node representation for AST Nodes 
    '''
    
    def __init__(self, name, lineno, ast_node=None):
        self._name = name
        self._lineno = lineno
        # AST node that originated this 'NodeRep' representation
        self._ast_node = ast_node
        
    
    def _get_parent_nodes(self, startnode, nodetys=[phpast.Node]):
        '''
        Yields parent nodes of type `type`.
        
        @param nodetys: The types of nodes to yield. Default to list 
            containing base type.
        @param startnode: Start node. 
        '''
        parent = getattr(startnode, '_parent_node', None)
        while parent:
            if type(parent) in nodetys:
                yield parent
            parent = getattr(parent, '_parent_node', None)
    
    def _parse(self, node):
        yield node
        for f in getattr(node, 'fields', []):
            val = getattr(node, f)
            if isinstance(val, phpast.Node):
                val = [val]
            if type(val) is list:
                for ele in val:
                    ele._parent_node = node
                    for el in self._parse(ele):
                        yield el
    
    @property
    def lineno(self):
        return self._lineno
    
    @property
    def name(self):
        return self._name


class VariableDef(NodeRep):
    '''
    Representation for the AST Variable Definition.
        (...)
    '''
    
    USER_VARS = ('$_GET', '$_POST', '$_COOKIES', '$_REQUEST')
    
    def __init__(self, name, lineno, scope, ast_node=None):
        
        NodeRep.__init__(self, name, lineno, ast_node=ast_node)
        
        # Containing Scope.
        self._scope = scope
        # Parent Variable
        self._parent = None
        # Is this var controlled by user?
        self._controlled_by_user = None
        # Vulns this variable is safe for. 
        self._safe_for = []
        # Being 'root' means that this var doesn't depend on
        # any other variable.
        if name in VariableDef.USER_VARS:
            self._is_root = True
        else:
            self._is_root = None

    @property
    def is_root(self):
        '''
        A variable is root when it has no ancestor or when its ancestor's name
        is in USER_VARS
        '''
        if self._is_root is None:
            if self.parent:
                self._is_root = False
            else:
                self._is_root = True
        return self._is_root
    
    @property
    def parent(self):
        '''
        Get this var's parent variable
        '''
        if self._is_root:
            return None
        
        if self._parent is None:
            parent = self._get_ancestor_var(self._ast_node.expr)
            if parent:
                self._parent = self._scope.get_var(parent.name)
        return self._parent
    
    @property
    def controlled_by_user(self):
        '''
        Returns bool that indicates if this variable is tainted.
        '''
        
        cbusr = self._controlled_by_user
        
        if cbusr is None:
            if self.is_root:
                if self._name in VariableDef.USER_VARS:
                    cbusr = True
                else:
                    cbusr = False
            else:
                cbusr = self.parent.controlled_by_user
            
            self._controlled_by_user = cbusr

        return cbusr
    
    def __eq__(self, ovar):
        return self._scope == ovar._scope and \
                self._lineno == ovar.lineno and \
                self._name == ovar.name
    
    def __gt__(self, ovar):
        # This basically indicates precedence. Use it to know if a
        #  variable should override another one.
        return self._scope == ovar._scope and \
                self._name == ovar.name and \
                self._lineno > ovar.lineno or \
                self.controlled_by_user
    
    def __hash__(self):
        return hash(self._name)
    
    def is_tainted_for(self, vulnty):
        return not vulnty in self._safe_for
    
    def deps(self):
        '''
        Generator function. Yields this var's dependency.
        '''
        parent = self.parent
        while not parent.is_root:
            yield parent
            parent = parent.parent
    
    def _get_ancestor_var(self, node):
        '''
        Return ancestor Variable for this var.
        '''
        for n in self._parse(node):
            if type(n) == phpast.Variable:
                nodetys=[phpast.FunctionCall]
                for fc in self._get_parent_nodes(n, nodetys=nodetys):
                    vulnty = FuncCall.get_vulnty_for_sec(fc.name)
                    if vulnty:
                        self._safe_for.append(vulnty)
                return n
        return None

class FuncCall(NodeRep):
    '''
    Representation for FunctionCall AST node.
    '''
    
    IS_CLEAN = 'IS_CLEAN'
    
    # Potentially Vulnerable Functions Database
    PVFDB = {
        'OS_COMMANDING':
            ('system', 'exec', 'shell_exec'),
        'XSS':
            ('echo', 'print', 'printf', 'header'),
        'FILE_INCLUDE':
            ('include', 'include_once', 'require', 'require_once'),
        'FILE_DISCLOSURE':
            ('file_get_contents', 'file', 'fread', 'finfo_file'),
        }
    # Securing Functions Database
    SFDB = {
        'OS_COMMANDING': 
            ('escapeshellarg', 'escapeshellcmd'),
        'XSS':
            ('htmlentities', 'htmlspecialchars'),
        'SQL':
            ('addslashes', 'mysql_real_escape_string', 'mysqli_escape_string',
             'mysqli_real_escape_string')
        }
    
    def __init__(self, name, lineno, ast_node, scope):
        
        NodeRep.__init__(self, name, lineno, ast_node=ast_node)
        self._scope = scope
        self._vuln_type = self._find_vuln()
    
    @property
    def vuln_type(self):
        return self._vuln_type
    
    def _find_vuln(self):
        
        # TODO: Refactor this! See duplicate code above
        def get_var_nodes(node):
            if type(node) == phpast.Variable:
                varnodes.append(node)
            else:
                for f in node.fields:
                    val = getattr(node, f)
                    if isinstance(val, phpast.Node):
                        val = [val]
                    if type(val) is list:
                        for ele in val:
                            get_var_nodes(ele)
        
        varnodes = []
        get_var_nodes(self._ast_node)
        vulnty = FuncCall.get_vulnty_for(self._name)
        if vulnty:
            for var in varnodes:
                var = self._scope.get_var(var.name)
                if var and var.controlled_by_user and \
                    var.is_tainted_for(vulnty):
                    return vulnty
        return FuncCall.IS_CLEAN
    
    @staticmethod
    def get_vulnty_for(fname):
        '''
        Return the vuln. type for the given function name `fname`. Return None
        if not found.
        
        @param fname: Function name
        '''
        for vulnty, pvfnames in FuncCall.PVFDB.iteritems():
            if any(fname == pvfn for pvfn in pvfnames):
                return vulnty
        return None
    
    @staticmethod
    def get_vulnty_for_sec(sfname):
        '''
        Return the the vuln. type secured by `sfname`.
        
        @param sfname: Securing function name 
        '''
        for vulnty, sfnames in FuncCall.SFDB.iteritems():
            if any(sfname == sfn for sfn in sfnames):
                return vulnty
        return None

class Scope(object):
    
    def __init__(self, ast_node, parent_scope=None):
        # AST node that defines this scope 
        self._ast_node = ast_node
        self._parent_scope = parent_scope
        self._vars = {}
        
    def add_var(self, newvar):
        
        if newvar is None:
            raise ValueError, "Invalid value for parameter 'var': None"
        
        selfvars = self._vars
        newvarname = newvar.name
        varobj = selfvars.get(newvarname)
        if not varobj or newvar > varobj:
            selfvars[newvarname] = newvar
            # Now let the parent scope do his thing
            if self._parent_scope:
                self._parent_scope.add_var(newvar)
    
    def get_var(self, varname):
        var = self._vars.get(varname)
        if not var and self._parent_scope:
            var = self._parent_scope.get_var(varname)
        return var
    
    def get_all_vars(self):
        return self._vars.values()
    
    def __repr__(self):
        return "Scope [%s]" % ', '.join(v.name for v in self.get_all_vars())
    
    