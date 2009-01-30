# -*- coding: Latin-1 -*-
"""Graphviz's dot language Python interface.

This module provides with a full interface to create handle modify
and process graphs in Graphviz's dot language.

References:

pydot Homepage:	http://www.dkbza.org/pydot.html
Graphviz:	http://www.research.att.com/sw/tools/graphviz/
DOT Language:	http://www.research.att.com/~erg/graphviz/info/lang.html

Programmed and tested with Graphviz 1.16 and Python 2.3.4 on GNU/Linux
by Ero Carrera (c) 2004	[ero@dkbza.org]

Distributed under MIT license [http://opensource.org/licenses/mit-license.html].
"""

__author__ = 'Ero Carrera'
__version__ = '1.0.2'
__license__ = 'MIT'

import os
import re
import subprocess
import tempfile
import copy
try:
    import dot_parser
except Exception, e:
    print "Couldn't import dot_parser, loading of dot files will not be possible."
    


GRAPH_ATTRIBUTES = set( ['Damping', 'K', 'URL', 'bb', 'bgcolor', 'center', 'charset',
    'clusterrank', 'colorscheme', 'comment', 'compound', 'concentrate',
    'defaultdist', 'dim', 'diredgeconstraints', 'dpi', 'epsilon', 'esep',
    'fontcolor', 'fontname', 'fontnames', 'fontpath', 'fontsize', 'label',
    'labeljust', 'labelloc', 'landscape', 'layers', 'layersep', 'levelsgap',
    'lp', 'margin', 'maxiter', 'mclimit', 'mindist', 'mode', 'model',
    'mosek', 'nodesep', 'nojustify', 'normalize', 'nslimit', 'nslimit1', 'ordering',
    'orientation', 'outputorder', 'overlap', 'pack', 'packmode', 'pad',
    'page', 'pagedir', 'quantum', 'rankdir', 'ranksep', 'ratio', 'remincross',
    'resolution', 'root', 'rotate', 'searchsize', 'sep', 'showboxes', 'size',
    'splines', 'start', 'stylesheet', 'target', 'truecolor', 'viewport',
    'voro_margin'] + ['rank'] )


EDGE_ATTRIBUTES = set( ['URL', 'arrowhead', 'arrowsize', 'arrowtail', 'color',
    'colorscheme', 'comment', 'constraint', 'decorate', 'dir',
    'edgeURL', 'edgehref', 'edgetarget', 'edgetooltip',
    'fontcolor', 'fontname', 'fontsize', 'headURL', 'headclip',
    'headhref', 'headlabel', 'headport', 'headtarget',
    'headtooltip', 'href', 'label', 'labelURL', 'labelangle',
    'labeldistance', 'labelfloat', 'labelfontcolor',
    'labelfontname', 'labelfontsize', 'labelhref', 'labeltarget',
    'labeltooltip', 'layer', 'len', 'lhead', 'lp', 'ltail',
    'minlen', 'nojustify', 'pos', 'samehead', 'sametail',
    'showboxes', 'style', 'tailURL', 'tailclip', 'tailhref',
    'taillabel', 'tailport', 'tailtarget', 'tailtooltip',
    'target', 'tooltip', 'weight'] + ['rank'] )


NODE_ATTRIBUTES = set( ['URL', 'color', 'colorscheme', 'comment',
    'distortion', 'fillcolor', 'fixedsize', 'fontcolor', 'fontname',
    'fontsize', 'group', 'height', 'image', 'imagescale', 'label',
    'layer', 'margin', 'nojustify', 'orientation', 'peripheries',
    'pin', 'pos', 'rects', 'regular', 'root', 'samplepoints',
    'shape', 'shapefile', 'showboxes', 'sides', 'skew', 'style',
    'target', 'tooltip', 'vertices', 'width', 'z',

    # The following are attributes dot2tex
    'texlbl',  'texmode' ] )


CLUSTER_ATTRIBUTES = set( ['K', 'URL', 'bgcolor', 'color', 'colorscheme', 'fillcolor',
    'fontcolor', 'fontname', 'fontsize', 'label', 'labeljust',
    'labelloc', 'lp', 'nojustify', 'pencolor', 'peripheries',
    'style', 'target', 'tooltip'] )
            

#
# Extented version of ASPN's Python Cookbook Recipe:
# Frozen dictionaries.
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/414283
#
# This version freezes dictionaries used as values within dictionaries.
#
class frozendict(dict):
    def _blocked_attribute(obj):
        raise AttributeError, "A frozendict cannot be modified."
    _blocked_attribute = property(_blocked_attribute)

    __delitem__ = __setitem__ = clear = _blocked_attribute
    pop = popitem = setdefault = update = _blocked_attribute

    def __new__(cls, *args, **kw):
        new = dict.__new__(cls)

        args_ = []
        for arg in args:
            if isinstance(arg, dict):
                arg = copy.copy(arg)
                for k, v in arg.items():
                    if isinstance(v, dict):
                        arg[k] = frozendict(v)
                    elif isinstance(v, list):
                        v_ = list()
                        for elm in v:
                            if isinstance(elm, dict):
                                v_.append( frozendict(elm) )
                            else:
                                v_.append( elm )
                        arg[k] = tuple(v_)
                args_.append( arg )
            else:
                args_.append( arg )

        dict.__init__(new, *args_, **kw)
        return new

    def __init__(self, *args, **kw):
        pass

    def __hash__(self):
        try:
            return self._cached_hash
        except AttributeError:
            h = self._cached_hash = hash(tuple(sorted(self.items())))
            return h

    def __repr__(self):
        return "frozendict(%s)" % dict.__repr__(self)


dot_keywords = ['graph', 'subgraph', 'digraph', 'node', 'edge', 'strict']

id_re_alpha_nums = re.compile('^[_a-zA-Z][a-zA-Z0-9_:,]*$')
id_re_num = re.compile('^[0-9]+$')
id_re_with_port = re.compile('^.*:([^"]+|[^"]*\"[^"]*\"[^"]*)$')
id_re_dbl_quoted = re.compile('^\".*\"$', re.S)
id_re_html = re.compile('^<.*>$', re.S)


def needs_quotes( s ):
    """Checks whether a string is a dot language ID.
    
    It will check whether the string is solely composed
    by the characters allowed in an ID or not.
    If the string is one of the reserved keywords it will
    need quotes too.
    """
        
    if s in dot_keywords:
        return False

    chars = [ord(c) for c in s if ord(c)>0x7f or ord(c)==0]
    if chars:
        return False
        
    res = id_re_alpha_nums.match(s)
    if not res:
        res = id_re_num.match(s)
        if not res:
            res = id_re_dbl_quoted.match(s)
            if not res:
                res = id_re_html.match(s)
                if not res:
                    res = id_re_with_port.match(s)

    if not res:
        return True

    return False



def quote_if_necessary(s):

    if not isinstance( s, basestring ):
        return s

    if needs_quotes(s):
            
        return '"' + s + '"'
     
    return s   



def graph_from_dot_data(data):
    """Load graph as defined by data in DOT format.
    
    The data is assumed to be in DOT format. It will
    be parsed and a Dot class will be returned, 
    representing the graph.
    """
    
    return dot_parser.parse_dot_data(data)


def graph_from_dot_file(path):
    """Load graph as defined by a DOT file.
    
    The file is assumed to be in DOT format. It will
    be loaded, parsed and a Dot class will be returned, 
    representing the graph.
    """
    
    fd = file(path, 'rb')
    data = fd.read()
    fd.close()
    
    return graph_from_dot_data(data)



def graph_from_edges(edge_list, node_prefix='', directed=False):
    """Creates a basic graph out of an edge list.
    
    The edge list has to be a list of tuples representing
    the nodes connected by the edge.
    The values can be anything: bool, int, float, str.
    
    If the graph is undirected by default, it is only
    calculated from one of the symmetric halves of the matrix.
    """
    
    if directed:
        graph = Dot(graph_type='digraph')
        
    else:
        graph = Dot(graph_type='graph')
        
    for edge in edge_list:

        e = Edge( node_prefix + edge[0], node_prefix + edge[1] )
        graph.add_edge(e)
        
    return graph


def graph_from_adjacency_matrix(matrix, node_prefix= u'', directed=False):
    """Creates a basic graph out of an adjacency matrix.
    
    The matrix has to be a list of rows of values
    representing an adjacency matrix.
    The values can be anything: bool, int, float, as long
    as they can evaluate to True or False.
    """
    
    node_orig = 1
    
    if directed:
        graph = Dot(graph_type='digraph')
    else:
        graph = Dot(graph_type='graph')
        
    for row in matrix:
        if not directed:
            skip = matrix.index(row)
            r = row[skip:]
        else:
            skip = 0
            r = row
        node_dest = skip+1
        
        for e in r:
            if e:
                graph.add_edge(
                    Edge( node_prefix + node_orig, 
                        node_prefix + node_dest) )
            node_dest += 1
        node_orig += 1
        
    return graph



def graph_from_incidence_matrix(matrix, node_prefix='', directed=False):
    """Creates a basic graph out of an incidence matrix.
    
    The matrix has to be a list of rows of values
    representing an incidence matrix.
    The values can be anything: bool, int, float, as long
    as they can evaluate to True or False.
    """
    
    node_orig = 1
    
    if directed:
        graph = Dot(graph_type='digraph')
    else:
        graph = Dot(graph_type='graph')
        
    for row in matrix:
        nodes = []
        c = 1
        
        for node in row:
            if node:
                nodes.append(c*node)
            c += 1
            nodes.sort()
            
        if len(nodes) == 2:
            graph.add_edge(	
                Edge( node_prefix + abs(nodes[0]),	
                    node_prefix + nodes[1] ))

    if not directed:
        graph.set_simplify(True)

    return graph

            


def __find_executables(path):
    """Used by find_graphviz
    
    path - single directory as a string
    
    If any of the executables are found, it will return a dictionary
    containing the program names as keys and their paths as values.
    
    Otherwise returns None
    """
    
    success = False
    progs = {'dot': '', 'twopi': '', 'neato': '', 'circo': '', 'fdp': ''}
    
    was_quoted = False
    path = path.strip()
    if path.startswith('"') and path.endswith('"'):
        path = path[1:-1]
        was_quoted =  True
    
    if os.path.isdir(path) : 
    
        for prg in progs.keys():
    
            if progs[prg]:
                continue
               
            if os.path.exists( os.path.join(path, prg) ):
                
                if was_quoted:
                    progs[prg] = '"' + os.path.join(path, prg) + '"'
                else:
                    progs[prg] = os.path.join(path, prg)
                    
                success = True
               
            elif os.path.exists( os.path.join(path, prg + '.exe') ):

                if was_quoted:
                    progs[prg] = '"' + os.path.join(path, prg + '.exe') + '"'
                else:
                    progs[prg] = os.path.join(path, prg + '.exe')
                    
                success = True
    
    if success:
    
        return progs
        
    else:
    
        return None



# The multi-platform version of this 'find_graphviz' function was
# contributed by Peter Cock
#
def find_graphviz():
    """Locate Graphviz's executables in the system.
    
    Tries three methods:
    
    First: Windows Registry (Windows only)
    This requires Mark Hammond's pywin32 is installed.
    
    Secondly: Search the path
    It will look for 'dot', 'twopi' and 'neato' in all the directories
    specified in the PATH environment variable.
    
    Thirdly: Default install location (Windows only)
    It will look for 'dot', 'twopi' and 'neato' in the default install
    location under the "Program Files" directory.
    
    It will return a dictionary containing the program names as keys
    and their paths as values.
    
    If this fails, it returns None.
    """
    
    # Method 1 (Windows only)
    #
    if os.sys.platform == 'win32':
    
        try:
            import win32api, win32con
            
            # Get the GraphViz install path from the registry
            #
            hkey = win32api.RegOpenKeyEx( win32con.HKEY_LOCAL_MACHINE,
                "SOFTWARE\ATT\Graphviz", 0, win32con.KEY_QUERY_VALUE )
                
            path = win32api.RegQueryValueEx( hkey, "InstallPath" )[0]
            win32api.RegCloseKey( hkey )
            
            # Now append the "bin" subdirectory:
            #
            path = os.path.join(path, "bin")
            progs = __find_executables(path)
            if progs is not None :
                #print "Used Windows registry"
                return progs
                
        except ImportError :
            # Print a messaged suggesting they install these?
            #
            pass

    # Method 2 (Linux, Windows etc)
    #
    if os.environ.has_key('PATH'):
    
        for path in os.environ['PATH'].split(os.pathsep):
            progs = __find_executables(path)
            if progs is not None :
                #print "Used path"
                return progs

    # Method 3 (Windows only)
    #
    if os.sys.platform == 'win32':
    
        # Try and work out the equivalent of "C:\Program Files" on this
        # machine (might be on drive D:, or in a different language)
        #
        
        if os.environ.has_key('PROGRAMFILES'):
        
            # Note, we could also use the win32api to get this
            # information, but win32api may not be installed.
            
            path = os.path.join(os.environ['PROGRAMFILES'], 'ATT', 'GraphViz', 'bin')
            
        else:
        
            #Just in case, try the default...
            path = r"C:\Program Files\att\Graphviz\bin"
            
        progs = __find_executables(path)
        
        if progs is not None :
        
            #print "Used default install location"
            return progs


    for path in (
        '/usr/bin', '/usr/local/bin',
        '/opt/bin', '/sw/bin', '/usr/share',
        '/Applications/Graphviz.app/Contents/MacOS/' ):
        
        progs = __find_executables(path)
        if progs is not None :
            #print "Used path"
            return progs

    # Failed to find GraphViz
    #
    return None
    

class Common:
    """Common information to several classes.
    
    Should not be directly used, several classes are derived from
    this one.
    """
    

    def __getstate__(self):

        dict = copy.copy(self.__dict__)
        for attr in self.attributes.keys():

            del dict['set_'+attr]
            del dict['get_'+attr]
   
        return dict

    
    def __setstate__(self, state):
    
        for k, v in state.items():
        
            self.__setattr__(k, v)


    def __get_attribute__(self, attr):
        """Look for default attributes for this node"""
        
        attr_val = self.obj_dict['attributes'].get(attr, None)
        
        if attr_val is None:
            # get the defaults for nodes/edges
            
            default_node_name = self.obj_dict['type']
            
            # The defaults for graphs are set on a node named 'graph'
            if default_node_name in ('subgraph', 'digraph', 'cluster'):
                default_node_name = 'graph'
                
            defaults = self.get_parent_graph().get_node( default_node_name )
            if defaults:
                attr_val = defaults.obj_dict['attributes'].get(attr, None)
                if attr_val:
                    return attr_val
        else:
            return attr_val
            
        return None
    

    def set_parent_graph(self, parent_graph):
    
        self.obj_dict['parent_graph'] = parent_graph
        

    def get_parent_graph(self):
    
        return self.obj_dict.get('parent_graph', None)


    def set(self, name, value):
        """Set an attribute value by name.
        
        Given an attribute 'name' it will set its value to 'value'.
        There's always the possibility of using the methods:
        
            set_'name'(value)
            
        which are defined for all the existing attributes.
        """

        if self.obj_dict['attributes'].has_key(name):
            self.obj_dict['attributes'][name] = value
            return True
            
        # Attribute is not known
        #
        return False



    def get(self, name):
        """Get an attribute value by name.
        
        Given an attribute 'name' it will get its value.
        There's always the possibility of using the methods:
        
            get_'name'()
            
        which are defined for all the existing attributes.
        """

        return self.obj_dict['attributes'].get(name, None)
        

    def get_attributes(self):
        """"""
        
        return self.obj_dict['attributes']

        
    def set_sequence(self, seq):
    
        self.obj_dict['sequence'] = seq


    def get_sequence(self):
    
        return self.obj_dict['sequence']
        
        
    def create_attribute_methods(self, obj_attributes):
    
        #for attr in self.obj_dict['attributes']:
        for attr in obj_attributes:
        
            # Generate all the Setter methods.
            #
            self.__setattr__( 'set_'+attr, lambda x, a=attr : self.obj_dict['attributes'].__setitem__(a, x) )
            
            # Generate all the Getter methods.
            #
            self.__setattr__('get_'+attr, lambda a=attr : self.__get_attribute__(a))



class Error(Exception):
    """General error handling class.
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value


class InvocationException(Exception):
    """To indicate that a ploblem occurred while running any of the GraphViz executables.
    """
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value



class Node(object, Common):
    """A graph node.
    
    This class represents a graph's node with all its attributes.
    
    node(name, attribute=value, ...)
    
    name: node's name
    
    All the attributes defined in the Graphviz dot language should
    be supported.
    """

    def __init__(self, name = '', obj_dict = None, **attrs):
    
        #
        # Nodes will take attributes of all other types because the defaults
        # for any GraphViz object are dealt with as if they were Node definitions
        #
        
        if obj_dict is not None:
        
            self.obj_dict = obj_dict
            
        else:
        
            self.obj_dict = dict()
            
            # Copy the attributes
            #
            self.obj_dict[ 'attributes' ] = dict( attrs )
            self.obj_dict[ 'type' ] = 'node'
            self.obj_dict[ 'parent_graph' ] = None
            self.obj_dict[ 'parent_node_list' ] = None
            self.obj_dict[ 'sequence' ] = None
    
            # Remove the compass point
            #
            port = None
            if isinstance(name, basestring) and not name.startswith('"'):
                idx = name.find(':')
                if idx > 0:
                    name, port = name[:idx], name[idx:]

            if isinstance(name, (long, int)):
                name = str(name)
            
            self.obj_dict['name'] = quote_if_necessary( name )
            self.obj_dict['port'] = port
        
        self.create_attribute_methods(NODE_ATTRIBUTES)
        
    
    
    def set_name(self, node_name):
        """Set the node's name."""
        
        self.obj_dict['name'] = node_name
        
        
    def get_name(self):
        """Get the node's name."""
        
        return self.obj_dict['name']

    
    def get_port(self):
        """Get the node's port."""
        
        return self.obj_dict['port']


    def add_style(self, style):
    
        styles = self.obj_dict['attributes'].get('style', None)
        if not styles and style:
            styles = [ style ]
        else:
            styles = styles.split(',')
            styles.append( style )
        
        self.obj_dict['attributes']['style'] = ','.join( styles )
        

    def to_string(self):
        """Returns a string representation of the node in dot language.
        """
        
        
        # RMF: special case defaults for node, edge and graph properties.
        #
        node = quote_if_necessary(self.obj_dict['name'])

        node_attr = list()

        for attr, value in self.obj_dict['attributes'].items():
            node_attr.append( attr + '=' + quote_if_necessary(value) )
                
                
        # No point in having nodes setting any defaults if the don't set
        # any attributes...
        #
        if node in ('graph', 'node', 'edge') and len(node_attr) == 0:
            return ''
            
        node_attr = ', '.join(node_attr)

        if node_attr:
            node += ' [' + node_attr + ']'

        return node + ';'



class Edge(object,  Common ):
    """A graph edge.
    
    This class represents a graph's edge with all its attributes.
    
    edge(src, dst, attribute=value, ...)
    
    src: source node's name
    dst: destination node's name
    
    All the attributes defined in the Graphviz dot language should
    be supported.
    
 	Attributes can be set through the dynamically generated methods:
    
     set_[attribute name], i.e. set_label, set_fontname
     
    or using the instance's attributes:
    
     Edge.[attribute name], i.e. edge_instance.label, edge_instance.fontname
    """
    


    def __init__(self, src='', dst='', obj_dict=None, **attrs):
    
        if obj_dict is not None:
        
            self.obj_dict = obj_dict
            
        else:
        
            self.obj_dict = dict()
            
            # Copy the attributes
            #
            self.obj_dict[ 'attributes' ] = dict( attrs )
            self.obj_dict[ 'type' ] = 'edge'
            self.obj_dict[ 'parent_graph' ] = None
            self.obj_dict[ 'parent_edge_list' ] = None
            self.obj_dict[ 'sequence' ] = None

            if isinstance(src, Node):
                src = src.get_name()
                
            if isinstance(dst, Node):
                dst = dst.get_name()
    
            points = ( quote_if_necessary( src) , quote_if_necessary( dst) )
            
            self.obj_dict['points'] = points
            
        self.create_attribute_methods(EDGE_ATTRIBUTES)


    def get_source(self):
        """Get the edges source node name."""
    
        return self.obj_dict['points'][0]
        
        
    def get_destination(self):
        """Get the edge's destination node name."""
        
        return self.obj_dict['points'][1]
            
            
    def __eq__(self, edge):
        """Compare two edges.
        
        If the parent graph is directed, arcs linking
        node A to B are considered equal and A->B != B->A
        
        If the parent graph is undirected, any edge
        connecting two nodes is equal to any other
        edge connecting the same nodes, A->B == B->A
        """
        
        if not isinstance(edge, Edge):
            raise Error, "Can't compare and edge to a non-edge object."
            
        if self.get_parent_graph().get_top_graph_type() == 'graph':
        
            # If the graph is undirected, the edge has neither
            # source nor destination.
            #
            if	( ( self.get_source()==edge.get_source() and self.get_destination()==edge.get_destination() ) or
                ( edge.get_source() == get_destination() and self.get_destination() == edge.get_source() ) ):
                return True
                
        else:
        
            if self.get_source()==edge.get_source() and self.get_destination()==edge.get_destination() :
                return True
                
        return False

        
    
    def parse_node_ref(self, node_str):
    
        if not isinstance(node_str, str):
            return node_str
    
        if node_str.startswith('"') and node_str.endswith('"') and node_str.count('"') % 2 != 0:
        
            return node_str
        
        node_port_idx = node_str.rfind(':')
        
        if node_port_idx>0 and node_str[0]=='"' and node_str[node_port_idx-1]=='"':
        
            return node_str
                
        if node_port_idx>0:
        
            a = node_str[:node_port_idx]
            b = node_str[node_port_idx+1:]

            node = quote_if_necessary(a)

            node += ':'+quote_if_necessary(b)

            return node
            
        return node_str
        
    
    def to_string(self):
        """Returns a string representation of the edge in dot language.
        """

        src = self.parse_node_ref( self.get_source() )
        dst = self.parse_node_ref( self.get_destination() )
        
        if isinstance(src, frozendict):
            edge = [ Subgraph(obj_dict=src).to_string() ]
        else:
            edge = [ src ]
        
        if	(self.get_parent_graph() and
            self.get_parent_graph().get_top_graph_type() and
            self.get_parent_graph().get_top_graph_type() == 'digraph' ):
            
            edge.append( '->' )
            
        else:
        
            edge.append( '--' )
            
        if isinstance(dst, frozendict):
            edge.append( Subgraph(obj_dict=dst).to_string() )
        else:
            edge.append( dst )


        edge_attr = list()
        
        for attr, value in self.obj_dict['attributes'].items():
        
            edge_attr.append( attr + '=' + quote_if_necessary(value) )

        edge_attr = ', '.join(edge_attr)
        
        if edge_attr:
            edge.append( ' [' + edge_attr + ']' )
            
        return ' '.join(edge) + ';'
    
    
    
    
    
class Graph(object, Common):
    """Class representing a graph in Graphviz's dot language.

    This class implements the methods to work on a representation
    of a graph in Graphviz's dot language.
    
    graph(  graph_name='G', graph_type='digraph',
        strict=False, suppress_disconnected=False, attribute=value, ...)
    
    graph_name:
        the graph's name
    graph_type:
        can be 'graph' or 'digraph'
    suppress_disconnected:
        defaults to False, which will remove from the
        graph any disconnected nodes.
    simplify:
        if True it will avoid displaying equal edges, i.e.
        only one edge between two nodes. removing the
        duplicated ones.
        
    All the attributes defined in the Graphviz dot language should
    be supported.
    
    Attributes can be set through the dynamically generated methods:
    
     set_[attribute name], i.e. set_size, set_fontname
     
    or using the instance's attributes:
    
     Graph.[attribute name], i.e. graph_instance.label, graph_instance.fontname
    """
    

    def __init__(self, graph_name='G', obj_dict=None, graph_type='digraph', strict=False,
        suppress_disconnected=False, simplify=False, **attrs):

        if obj_dict is not None:
            self.obj_dict = obj_dict
            
        else:

            self.obj_dict = dict()
            
            self.obj_dict['attributes'] = dict(attrs)
            
            if graph_type not in ['graph', 'digraph']:
                raise Error, 'Invalid type "%s". Accepted graph types are: graph, digraph, subgraph' % graph_type
    
    
            self.obj_dict['name'] = graph_name
            self.obj_dict['type'] = graph_type
            
            self.obj_dict['strict'] = strict
            self.obj_dict['suppress_disconnected'] = suppress_disconnected
            self.obj_dict['simplify'] = simplify
    
            self.obj_dict['current_child_sequence'] = 1
            self.obj_dict['nodes'] = dict()
            self.obj_dict['edges'] = dict()
            self.obj_dict['subgraphs'] = dict()

            self.set_parent_graph(self)
            

        self.create_attribute_methods(GRAPH_ATTRIBUTES)


    def get_graph_type(self):
    
        return self.obj_dict['type']


    def get_top_graph_type(self):
    
        parent = self
        while True:
            parent_ = parent.get_parent_graph()
            if parent_ == parent:
                break
            parent = parent_
    
        return parent.obj_dict['type']
                

    def set_graph_defaults(self, **attrs):

        self.add_node( Node('graph', **attrs) )


    def get_graph_defaults(self, **attrs):
    
        graph_nodes = self.get_node('graph')

        return [ node.get_attributes() for node in graph_nodes ]
        

    def set_node_defaults(self, **attrs):

        self.add_node( Node('node', **attrs) )


    def get_node_defaults(self, **attrs):
    
    
        graph_nodes = self.get_node('node')

        return [ node.get_attributes() for node in graph_nodes ]
        

    def set_edge_defaults(self, **attrs):

        self.add_node( Node('edge', **attrs) )



    def get_edge_defaults(self, **attrs):
    
        graph_nodes = self.get_node('edge')

        return [ node.get_attributes() for node in graph_nodes ]

    

    def set_simplify(self, simplify):
        """Set whether to simplify or not.
        
        If True it will avoid displaying equal edges, i.e.
        only one edge between two nodes. removing the
        duplicated ones.
        """
        
        self.obj_dict['simplify'] = simplify



    def get_simplify(self):
        """Get whether to simplify or not.
        
        Refer to set_simplify for more information.
        """
        
        return self.obj_dict['simplify']

            
    def set_type(self, graph_type):
        """Set the graph's type, 'graph' or 'digraph'."""

        self.obj_dict['type'] = graph_type


        
    def get_type(self):
        """Get the graph's type, 'graph' or 'digraph'."""

        return self.obj_dict['type']



    def set_name(self, graph_name):
        """Set the graph's name."""
        
        self.obj_dict['name'] = graph_name



    def get_name(self):
        """Get the graph's name."""
        
        return self.obj_dict['name']


                    
    def set_strict(self, val):
        """Set graph to 'strict' mode.
        
        This option is only valid for top level graphs.
        """
        
        self.obj_dict['strict'] = val



    def get_strict(self, val):
        """Get graph's 'strict' mode (True, False).
        
        This option is only valid for top level graphs.
        """
        
        return self.obj_dict['strict']
        


    def set_suppress_disconnected(self, val):
        """Suppress disconnected nodes in the output graph.
        
        This option will skip nodes in the graph with no	incoming or outgoing
        edges. This option works also for subgraphs and has effect only in the
        current graph/subgraph.
        """
        
        self.obj_dict['suppress_disconnected'] = val
            


    def get_suppress_disconnected(self, val):
        """Get if suppress disconnected is set.
        
        Refer to set_suppress_disconnected for more information.
        """
        
        return self.obj_dict['suppress_disconnected']
            

    def get_next_sequence_number(self):
    
        seq = self.obj_dict['current_child_sequence']
        
        self.obj_dict['current_child_sequence'] += 1
        
        return seq
        

    def add_node(self, graph_node):
        """Adds a node object to the graph.

        It takes a node object as its only argument and returns
        None.
        """
        
        if not isinstance(graph_node, Node):
            raise TypeError('add_node() received a non node class object')

            
        node = self.get_node(graph_node.get_name())
        
        if not node:

            self.obj_dict['nodes'][graph_node.get_name()] = [ graph_node.obj_dict ]
            
            #self.node_dict[graph_node.get_name()] = graph_node.attributes
            graph_node.set_parent_graph(self.get_parent_graph())
                
        else:
        
            self.obj_dict['nodes'][graph_node.get_name()].append( graph_node.obj_dict )

        graph_node.set_sequence(self.get_next_sequence_number())



    def get_node(self, name):
        """Retrieved a node from the graph.
        
        Given a node's name the corresponding Node
        instance will be returned.
        
        If multiple nodes exist with that name, a list of
        Node instances is returned.
        If only one node exists, the instance is returned.
        None is returned otherwise.
        """
        
        match = list()
        
        if self.obj_dict['nodes'].has_key(name):
        
            match.extend( [ Node( obj_dict = obj_dict ) for obj_dict in self.obj_dict['nodes'][name] ])
        
        if len(match)==1:
            return match[0]
            
        return match


    def get_nodes(self):
        """Return an iterator."""
        
        return self.get_node_list()
        
        
    def get_node_list(self):
        """Get the list of Node instances.
        
        This method returns the list of Node instances
        composing the graph.
        """
        
        node_objs = list()
        
        for node, obj_dict_list in self.obj_dict['nodes'].items():
                node_objs.extend( [ Node( obj_dict = obj_d ) for obj_d in obj_dict_list ] )
        
        return node_objs



    def add_edge(self, graph_edge):
        """Adds an edge object to the graph.
        
        It takes a edge object as its only argument and returns
        None.
        """

        if not isinstance(graph_edge, Edge):
            raise TypeError('add_edge() received a non edge class object')
            
        edge_points = ( graph_edge.get_source(), graph_edge.get_destination() )

        if self.obj_dict['edges'].has_key(edge_points):
        
            edge_list = self.obj_dict['edges'][edge_points]
            edge_list.append(graph_edge.obj_dict)
                
        else:
        
            self.obj_dict['edges'][edge_points] = [ graph_edge.obj_dict ]
         
        graph_edge.set_sequence( self.get_next_sequence_number() )
        
        graph_edge.set_parent_graph( self.get_parent_graph() )
            



    def get_edge(self, src, dst):
        """Retrieved an edge from the graph.
        
        Given an edge's source and destination the corresponding
        Edge instance will be returned.
        
        If multiple edges exist with that source and destination,
        a list of Edge instances is returned.
        If only one edge exists, the instance is returned.
        None is returned otherwise.
        """

        edge_points = (src, dst)
        

        match = list()
        
        if self.obj_dict['edges'].has_key( (src, dst) ) or (
            self.get_top_graph_type() == 'graph' and self.obj_dict['edges'].has_key( (dst, src) )):
        
            edges_obj_dict = self.obj_dict['edges'].get(
                (src, dst),
                self.obj_dict['edges'].get( (dst, src), None ))
        
            for edge_obj_dict in edges_obj_dict:
                match.append( Edge( edge_points[0], edge_points[1], obj_dict = edge_obj_dict ) )
        
        if len(match)==1:
            return match[0]
            
        return match


    def get_edges(self):
        return self.get_edge_list()
        
        
    def get_edge_list(self):
        """Get the list of Edge instances.
        
        This method returns the list of Edge instances
        composing the graph.
        """
        
        edge_objs = list()
        
        for edge, obj_dict_list in self.obj_dict['edges'].items():
                edge_objs.extend( [ Edge( obj_dict = obj_d ) for obj_d in obj_dict_list ] )
        
        return edge_objs


            
    def add_subgraph(self, sgraph):
        """Adds an subgraph object to the graph.
        
        It takes a subgraph object as its only argument and returns
        None.
        """

        if not isinstance(sgraph, Subgraph) and not isinstance(sgraph, Cluster):
            raise TypeError('add_subgraph() received a non subgraph class object')
            
        if self.obj_dict['subgraphs'].has_key(sgraph.get_name()):
        
            sgraph_list = self.obj_dict['subgraphs'][ sgraph.get_name() ]
            sgraph_list.append( sgraph.obj_dict )
                
        else:
            self.obj_dict['subgraphs'][ sgraph.get_name() ] = [ sgraph.obj_dict ]
         
        sgraph.set_sequence( self.get_next_sequence_number() )
        
        sgraph.set_parent_graph( self.get_parent_graph() )



    
    def get_subgraph(self, name):
        """Retrieved a subgraph from the graph.
        
        Given a subgraph's name the corresponding
        Subgraph instance will be returned.
        
        If multiple subgraphs exist with the same name,	a list of
        Subgraph instances is returned.
        If only one Subgraph exists, the instance is returned.
        None is returned otherwise.
        """
        
        match = None
        
        if self.obj_dict['subgraphs'].has_key( sgraph.get_name() ):
        
            sgraphs_obj_dict = self.obj_dict['subgraphs'].get( sgraph.get_name() )
        
            for obj_dict_list in sgraphs_obj_dict:
                match = [ Subgraph( obj_dict = obj_d ) for obj_d in obj_dict_list ]
        
        if len(match)==1:
            return match[0]
            
        return match


    def get_subgraphs(self):
    
        return get_subgraph_list()
        
        
    def get_subgraph_list(self):
        """Get the list of Subgraph instances.
        
        This method returns the list of Subgraph instances
        in the graph.
        """
        
        sgraph_objs = list()
        
        for sgraph, obj_dict_list in self.obj_dict['subgraphs'].items():
                sgraph_objs.extend( [ Subgraph( obj_dict = obj_d ) for obj_d in obj_dict_list ] )
        
        return sgraph_objs
            


    def set_parent_graph(self, parent_graph):
    
        self.obj_dict['parent_graph'] = parent_graph
        
        for obj_list in self.obj_dict['nodes'].values():
            for obj in obj_list:
                obj['parent_graph'] = parent_graph

        for obj_list in self.obj_dict['edges'].values():
            for obj in obj_list:
                obj['parent_graph'] = parent_graph

        for obj_list in self.obj_dict['subgraphs'].values():
            for obj in obj_list:
                Graph(obj_dict=obj).set_parent_graph(parent_graph)



    def to_string(self):
        """Returns a string representation of the graph in dot language.
        
        It will return the graph and all its subelements in string from.
        """
        
        
        graph = list()
        
        if self.obj_dict.get('strict', None) is not None:
        
            if self==self.get_parent_graph() and self.obj_dict['strict']:
            
                graph.append('strict ')
        
        if self.obj_dict['name'] == '':
            graph.append( '{\n' )
        else:
            graph.append( '%s %s {\n' % (self.obj_dict['type'], self.obj_dict['name']) )


        for attr in self.obj_dict['attributes'].keys():
        
            if self.obj_dict['attributes'].get(attr, None) is not None:
       
                graph.append( '%s=' % attr )
                val = self.obj_dict['attributes'].get(attr)
                
                graph.append( quote_if_necessary(val) )
                    
                graph.append( ';\n' )


        edges_done = set()
        
        edge_obj_dicts = list()
        for e in self.obj_dict['edges'].values():
            edge_obj_dicts.extend(e)
            
        if edge_obj_dicts:
            edge_src_set, edge_dst_set = zip( *[obj['points'] for obj in edge_obj_dicts] )
            edge_src_set, edge_dst_set = set(edge_src_set), set(edge_dst_set)
        else:
            edge_src_set, edge_dst_set = set(), set()
            
        node_obj_dicts = list()
        for e in self.obj_dict['nodes'].values():
            node_obj_dicts.extend(e)

        sgraph_obj_dicts = list()
        for sg in self.obj_dict['subgraphs'].values():
            sgraph_obj_dicts.extend(sg)

        
        obj_list = [ (obj['sequence'], obj) for obj in (edge_obj_dicts + node_obj_dicts + sgraph_obj_dicts) ]
        obj_list.sort()
        
        for idx, obj in obj_list:
        
            if obj['type'] == 'node':

                node = Node(obj_dict=obj)
            
                if self.obj_dict.get('suppress_disconnected', False):
                
                    if (node.get_name() not in edge_src_set and
                        node.get_name() not in edge_dst_set):
                        
                        continue
                        
                graph.append( node.to_string()+'\n' )

            elif obj['type'] == 'edge':

                edge = Edge(obj_dict=obj)
                
                if self.obj_dict.get('simplify', False) and elm in edges_done:
                    continue
                
                graph.append( edge.to_string() + '\n' )
                edges_done.add(edge)
                
            else:
            
                sgraph = Subgraph(obj_dict=obj)
                
                graph.append( sgraph.to_string()+'\n' )

        graph.append( '}\n' )
        
        return ''.join(graph)



class Subgraph(Graph):

    """Class representing a subgraph in Graphviz's dot language.

    This class implements the methods to work on a representation
    of a subgraph in Graphviz's dot language.
    
    subgraph(graph_name='subG', suppress_disconnected=False, attribute=value, ...)
    
    graph_name:
        the subgraph's name
    suppress_disconnected:
        defaults to false, which will remove from the
        subgraph any disconnected nodes.
    All the attributes defined in the Graphviz dot language should
    be supported.
    
    Attributes can be set through the dynamically generated methods:
    
     set_[attribute name], i.e. set_size, set_fontname
     
    or using the instance's attributes:
    
     Subgraph.[attribute name], i.e.
     	subgraph_instance.label, subgraph_instance.fontname
    """
    
    
    # RMF: subgraph should have all the attributes of graph so it can be passed
    # as a graph to all methods
    #
    def __init__(self, graph_name='', obj_dict=None, suppress_disconnected=False,
        simplify=False, **attrs):
        

        Graph.__init__(self, graph_name=graph_name, obj_dict=obj_dict,
            suppress_disconnected=suppress_disconnected, simplify=simplify, **attrs)

        if obj_dict is None:

            self.obj_dict['type'] = 'subgraph'




class Cluster(Graph):

    """Class representing a cluster in Graphviz's dot language.

    This class implements the methods to work on a representation
    of a cluster in Graphviz's dot language.
    
    cluster(graph_name='subG', suppress_disconnected=False, attribute=value, ...)
    
    graph_name:
        the cluster's name (the string 'cluster' will be always prepended)
    suppress_disconnected:
        defaults to false, which will remove from the
        cluster any disconnected nodes.
    All the attributes defined in the Graphviz dot language should
    be supported.
    
    Attributes can be set through the dynamically generated methods:
    
     set_[attribute name], i.e. set_color, set_fontname
     
    or using the instance's attributes:
    
     Cluster.[attribute name], i.e.
     	cluster_instance.color, cluster_instance.fontname
    """
    

    def __init__(self, graph_name='subG', obj_dict=None, suppress_disconnected=False,
        simplify=False, **attrs):

        Graph.__init__(self, graph_name=graph_name, obj_dict=obj_dict,
            suppress_disconnected=suppress_disconnected, simplify=simplify, **attrs)

        if obj_dict is None:

            self.obj_dict['type'] = 'subgraph'
            self.obj_dict['name'] = 'cluster_'+graph_name



   


class Dot(Graph):
    """A container for handling a dot language file.

    This class implements methods to write and process
    a dot language file. It is a derived class of
    the base class 'Graph'.
    """
    
    
     
    def __init__(self, *argsl, **argsd):
        Graph.__init__(self, *argsl, **argsd)

        self.shape_files = list()

        self.progs = None
        
        self.formats = ['canon', 'cmap', 'cmapx', 'cmapx_np', 'dia', 'dot',
            'fig', 'gd', 'gd2', 'gif', 'hpgl', 'imap', 'imap_np', 'ismap',
            'jpe', 'jpeg', 'jpg', 'mif', 'mp', 'pcl', 'pdf', 'pic', 'plain',
            'plain-ext', 'png', 'ps', 'ps2', 'svg', 'svgz', 'vml', 'vmlz',
            'vrml', 'vtx', 'wbmp', 'xdot', 'xlib' ]

        self.prog = 'dot'
        
        # Automatically creates all the methods enabling the creation
        # of output in any of the supported formats.
        for frmt in self.formats:
            self.__setattr__(
                'create_'+frmt,
                lambda f=frmt, prog=self.prog : self.create(format=f, prog=prog))
            f = self.__dict__['create_'+frmt]
            f.__doc__ = '''Refer to the docstring accompanying the 'create' method for more information.'''
            
        for frmt in self.formats+['raw']:
            self.__setattr__(
                'write_'+frmt,
                lambda path, f=frmt, prog=self.prog : self.write(path, format=f, prog=prog))
                
            f = self.__dict__['write_'+frmt]
            f.__doc__ = '''Refer to the docstring accompanying the 'write' method for more information.'''

    
            
    def __getstate__(self):

        dict = copy.copy(self.__dict__)
        for attr in self.attributes:
            del dict['set_'+attr]
            del dict['get_'+attr]
   			
        for k in [ x for x in dict.keys() if
            x.startswith('write_') or  x.startswith('create_') ]:
            
            del dict[k]
   
        return dict
    
    
    def set_shape_files(self, file_paths):
        """Add the paths of the required image files.
        
        If the graph needs graphic objects to be used as shapes or otherwise
        those need to be in the same folder as the graph is going to be rendered
        from. Alternatively the absolute path to the files can be specified when
        including the graphics in the graph.
        
        The files in the location pointed to by the path(s) specified as arguments
        to this method will be copied to the same temporary location where the
        graph is going to be rendered.
        """
        
        if isinstance( file_paths, basestring ):
            self.shape_files.append( file_paths )
            
        if isinstance( file_paths, (list, tuple) ):
            self.shape_files.extend( file_paths )
    
                
    def set_prog(self, prog):
        """Sets the default program.
        
        Sets the default program in charge of processing
        the dot file into a graph.
        """
        self.prog = prog
        

    def set_graphviz_executables(self, paths):
        """This method allows to manually specify the location of the GraphViz executables.
        
        The argument to this method should be a dictionary where the keys are as follows:
        
            {'dot': '', 'twopi': '', 'neato': '', 'circo': '', 'fdp': ''}
            
        and the values are the paths to the corresponding executable, including the name
        of the executable itself.
        """
    
        self.progs = paths


    def write(self, path, prog=None, format='raw'):
        """Writes a graph to a file.

        Given a filename 'path' it will open/create and truncate
        such file and write on it a representation of the graph
        defined by the dot object and in the format specified by
        'format'.
        The format 'raw' is used to dump the string representation
        of the Dot object, without further processing.
        The output can be processed by any of graphviz tools, defined
        in 'prog', which defaults to 'dot'
        Returns True or False according to the success of the write
        operation.
        
        There's also the preferred possibility of using:
        
            write_'format'(path, prog='program')
            
        which are automatically defined for all the supported formats.
        [write_ps(), write_gif(), write_dia(), ...]
        """

        if prog is None:
            prog = self.prog
        
        dot_fd = file(path, "w+b")
        if format == 'raw':
            dot_fd.write(self.to_string())
        else:
            dot_fd.write(self.create(prog, format))
        dot_fd.close()

        return True
        


    def create(self, prog=None, format='ps'):
        """Creates and returns a Postscript representation of the graph.

        create will write the graph to a temporary dot file and process
        it with the program given by 'prog' (which defaults to 'twopi'),
        reading the Postscript output and returning it as a string is the
        operation is successful.
        On failure None is returned.
        
        There's also the preferred possibility of using:
        
            create_'format'(prog='program')
            
        which are automatically defined for all the supported formats.
        [create_ps(), create_gif(), create_dia(), ...]
        """
        
        if prog is None:
            prog = self.prog
            
        if self.progs is None:
            self.progs = find_graphviz()
            if self.progs is None:
                raise InvocationException(
                    'GraphViz\'s executables not found' )
                
        if not self.progs.has_key(prog):
            raise InvocationException(
                'GraphViz\'s executable "%s" not found' % prog )
            
        if not os.path.exists( self.progs[prog] ) or not os.path.isfile( self.progs[prog] ):
            raise InvocationException(
                'GraphViz\'s executable "%s" is not a file or doesn\'t exist' % self.progs[prog] )
            
            
        tmp_fd, tmp_name = tempfile.mkstemp()
        os.close(tmp_fd)
        self.write(tmp_name)
        tmp_dir = os.path.dirname(tmp_name )
        
        # For each of the image files...
        #
        for img in self.shape_files:
        
            # Get its data
            #
            f = file(img, 'rb')
            f_data = f.read()
            f.close()
            
            # And copy it under a file with the same name in the temporary directory
            #
            f = file( os.path.join( tmp_dir, os.path.basename(img) ), 'wb' )
            f.write(f_data)
            f.close()

        p = subprocess.Popen(
            (self.progs[prog], '-T'+format, tmp_name),
            cwd=tmp_dir,
            stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            
        stderr = p.stderr
        stdout = p.stdout
        
        stdout_output = list()
        while True:
            data = stdout.read()
            if not data:
                break
            stdout_output.append(data)
        stdout.close()
            
        if stdout_output:
            stdout_output = ''.join(stdout_output)
        
        if not stderr.closed:
            stderr_output = list()
            while True:
                data = stderr.read()
                if not data:
                    break
                stderr_output.append(data)
            stderr.close()
                
            if stderr_output:
                stderr_output = ''.join(stderr_output)
            
        #pid, status = os.waitpid(p.pid, 0)
        status = p.wait()
        
        if status != 0 :
            raise InvocationException(
                'Program terminated with status: %d. stderr follows: %s' % (
                    status, stderr_output) )
        elif stderr_output:
            print stderr_output
        
        # For each of the image files...
        #
        for img in self.shape_files:
        
            # remove it
            #
            os.unlink( os.path.join( tmp_dir, os.path.basename(img) ) )

        os.unlink(tmp_name)
        
        return stdout_output

