#! /usr/bin/env python
"""Compatibility module, imported by ZSI if you don't have PyXML 0.7.

No copyright violations -- we're only using parts of PyXML that we
wrote.
"""

_copyright = '''ZSI:  Zolera Soap Infrastructure.

Copyright 2001, Zolera Systems, Inc.  All Rights Reserved.
Copyright 2002-2003, Rich Salz. All Rights Reserved.

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, and/or
sell copies of the Software, and to permit persons to whom the Software
is furnished to do so, provided that the above copyright notice(s) and
this permission notice appear in all copies of the Software and that
both the above copyright notice(s) and this permission notice appear in
supporting documentation.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT
OF THIRD PARTY RIGHTS. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR HOLDERS
INCLUDED IN THIS NOTICE BE LIABLE FOR ANY CLAIM, OR ANY SPECIAL INDIRECT
OR CONSEQUENTIAL DAMAGES, OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS
OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE
OR OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE
OR PERFORMANCE OF THIS SOFTWARE.

Except as contained in this notice, the name of a copyright holder
shall not be used in advertising or otherwise to promote the sale, use
or other dealings in this Software without prior written authorization
of the copyright holder.
'''

_copyright += "\n\nPortions are also: "
_copyright += '''Copyright 2001, Zolera Systems Inc.  All Rights Reserved.
Copyright 2001, MIT. All Rights Reserved.

Distributed under the terms of:
  Python 2.0 License or later.
  http://www.python.org/2.0.1/license.html
or
  W3C Software License
  http://www.w3.org/Consortium/Legal/copyright-software-19980720
'''

from xml.dom import Node
from Namespaces import XMLNS
import cStringIO as StringIO
try: 
    from xml.dom.ext import c14n
except ImportError, ex:
    _implementation2 = None
    _attrs = lambda E: (E.attributes and E.attributes.values()) or []
    _children = lambda E: E.childNodes or []
else:
    class _implementation2(c14n._implementation):
        """Patch for exclusive c14n 
        """
        def __init__(self, node, write, **kw):
            self.unsuppressedPrefixes = kw.get('unsuppressedPrefixes')
            self._exclusive = None
            if node.nodeType == Node.ELEMENT_NODE:
                if not c14n._inclusive(self):
                    self._exclusive = self._inherit_context(node)
            c14n._implementation.__init__(self, node, write, **kw)

        def _do_element(self, node, initial_other_attrs = []):
            """Patch for the xml.dom.ext.c14n implemenation _do_element method.
            This fixes a problem with sorting of namespaces.
            """
            # Get state (from the stack) make local copies.
            #   ns_parent -- NS declarations in parent
            #   ns_rendered -- NS nodes rendered by ancestors
            #        ns_local -- NS declarations relevant to this element
            #   xml_attrs -- Attributes in XML namespace from parent
            #       xml_attrs_local -- Local attributes in XML namespace.
            ns_parent, ns_rendered, xml_attrs = \
        	    self.state[0], self.state[1].copy(), self.state[2].copy() #0422
            ns_local = ns_parent.copy()
            xml_attrs_local = {}

            # Divide attributes into NS, XML, and others.
            #other_attrs = initial_other_attrs[:]
            other_attrs = []
            sort_these_attrs = initial_other_attrs[:]

            in_subset = c14n._in_subset(self.subset, node)
            #for a in _attrs(node):
            sort_these_attrs +=c14n._attrs(node)
            
            for a in sort_these_attrs:
        	if a.namespaceURI == c14n.XMLNS.BASE:
        	    n = a.nodeName
        	    if n == "xmlns:": n = "xmlns"        # DOM bug workaround
        	    ns_local[n] = a.nodeValue
        	elif a.namespaceURI == c14n.XMLNS.XML:
        	    if c14n._inclusive(self) or (in_subset and  c14n._in_subset(self.subset, a)): #020925 Test to see if attribute node in subset
        		xml_attrs_local[a.nodeName] = a #0426
        	else:
        	    if  c14n._in_subset(self.subset, a):     #020925 Test to see if attribute node in subset
        		other_attrs.append(a)
        	#add local xml:foo attributes to ancestor's xml:foo attributes
        	xml_attrs.update(xml_attrs_local)

            # Render the node
            W, name = self.write, None
            if in_subset: 
        	name = node.nodeName
        	W('<')
        	W(name)

        	# Create list of NS attributes to render.
        	ns_to_render = []
        	for n,v in ns_local.items():

        	    # If default namespace is XMLNS.BASE or empty,
        	    # and if an ancestor was the same
        	    if n == "xmlns" and v in [ c14n.XMLNS.BASE, '' ] \
        	    and ns_rendered.get('xmlns') in [ c14n.XMLNS.BASE, '', None ]:
        		continue

        	    # "omit namespace node with local name xml, which defines
        	    # the xml prefix, if its string value is
        	    # http://www.w3.org/XML/1998/namespace."
        	    if n in ["xmlns:xml", "xml"] \
        	    and v in [ 'http://www.w3.org/XML/1998/namespace' ]:
        		continue


        	    # If not previously rendered
        	    # and it's inclusive  or utilized
        	    if (n,v) not in ns_rendered.items() \
        	      and (c14n._inclusive(self) or \
        	      c14n._utilized(n, node, other_attrs, self.unsuppressedPrefixes)):
        		ns_to_render.append((n, v))

                #####################################
                # JRB
                #####################################
                if not c14n._inclusive(self):
                    if node.prefix is None:
                        look_for = [('xmlns', node.namespaceURI),]
                    else:
                        look_for = [('xmlns:%s' %node.prefix, node.namespaceURI),]
                    for a in c14n._attrs(node):
                        if a.namespaceURI != XMLNS.BASE:
                           #print "ATTRIBUTE: ", (a.namespaceURI, a.prefix)
                           if a.prefix:
                               #print "APREFIX: ", a.prefix
                               look_for.append(('xmlns:%s' %a.prefix, a.namespaceURI))

                    for key,namespaceURI in look_for:
                        if ns_rendered.has_key(key):
                            if ns_rendered[key] == namespaceURI:
                                # Dont write out
                                pass
                            else:
                                #ns_to_render += [(key, namespaceURI)]
                                pass
                        elif (key,namespaceURI) in ns_to_render:
                            # Dont write out
                            pass
                        else:
                            # Unique write out, rewrite to render
                            ns_local[key] = namespaceURI
                            for a in self._exclusive:
                                if a.nodeName == key:
                                    #self._do_attr(a.nodeName, a.value)
                                    #ns_rendered[key] = namespaceURI
                                    #break
                                    ns_to_render += [(a.nodeName, a.value)]
                                    break
                                elif key is None and a.nodeName == 'xmlns':
                                    #print "DEFAULT: ", (a.nodeName, a.value)
                                    ns_to_render += [(a.nodeName, a.value)]
                                    break
                                #print "KEY: ", key
                            else:
                                #print "Look for: ", look_for
                                #print "NS_TO_RENDER: ", ns_to_render
                                #print "EXCLUSIVE NS: ", map(lambda f: (f.nodeName,f.value),self._exclusive)
                                raise RuntimeError, \
                                   'can not find namespace (%s="%s")  for exclusive canonicalization'\
                                   %(key, namespaceURI)
                #####################################



        	# Sort and render the ns, marking what was rendered.
        	ns_to_render.sort(c14n._sorter_ns)
        	for n,v in ns_to_render:
        	    #XXX JRB, getting 'xmlns,None' here when xmlns=''
        	    if v: self._do_attr(n, v)
        	    else:
        		v = ''
        		self._do_attr(n, v)
        	    ns_rendered[n]=v    #0417

        	# If exclusive or the parent is in the subset, add the local xml attributes
        	# Else, add all local and ancestor xml attributes
        	# Sort and render the attributes.
        	if not c14n._inclusive(self) or c14n._in_subset(self.subset,node.parentNode):  #0426
        	    other_attrs.extend(xml_attrs_local.values())
        	else:
        	    other_attrs.extend(xml_attrs.values())
                #print "OTHER: ", other_attrs
        	other_attrs.sort(c14n._sorter)
        	for a in other_attrs:
        	    self._do_attr(a.nodeName, a.value)
                W('>')


            # Push state, recurse, pop state.
            state, self.state = self.state, (ns_local, ns_rendered, xml_attrs)
            for c in c14n._children(node):
        	c14n._implementation.handlers[c.nodeType](self, c)
            self.state = state

            if name: W('</%s>' % name)
        c14n._implementation.handlers[c14n.Node.ELEMENT_NODE] = _do_element


_IN_XML_NS = lambda n: n.namespaceURI == XMLNS.XML

# Does a document/PI has lesser/greater document order than the
# first element?
_LesserElement, _Element, _GreaterElement = range(3)

def _sorter(n1,n2):
    '''_sorter(n1,n2) -> int
    Sorting predicate for non-NS attributes.'''

    i = cmp(n1.namespaceURI, n2.namespaceURI)
    if i: return i
    return cmp(n1.localName, n2.localName)


def _sorter_ns(n1,n2):
    '''_sorter_ns((n,v),(n,v)) -> int
    "(an empty namespace URI is lexicographically least)."'''

    if n1[0] == 'xmlns': return -1
    if n2[0] == 'xmlns': return 1
    return cmp(n1[0], n2[0])

def _utilized(n, node, other_attrs, unsuppressedPrefixes):
    '''_utilized(n, node, other_attrs, unsuppressedPrefixes) -> boolean
    Return true if that nodespace is utilized within the node'''

    if n.startswith('xmlns:'):
        n = n[6:]
    elif n.startswith('xmlns'):
        n = n[5:]
    if n == node.prefix or n in unsuppressedPrefixes: return 1
    for attr in other_attrs:
        if n == attr.prefix: return 1
    return 0

_in_subset = lambda subset, node: not subset or node in subset

#
# JRB. Currently there is a bug in do_element, but since the underlying
# Data Structures in c14n have changed I can't just apply the
# _implementation2 patch above.  But this will work OK for most uses,
# just not XML Signatures.
#
class _implementation:
    '''Implementation class for C14N. This accompanies a node during it's
    processing and includes the parameters and processing state.'''

    # Handler for each node type; populated during module instantiation.
    handlers = {}

    def __init__(self, node, write, **kw):
        '''Create and run the implementation.'''

        self.write = write
        self.subset = kw.get('subset')
        if self.subset:
            self.comments = kw.get('comments', 1)
        else:
            self.comments = kw.get('comments', 0)
        self.unsuppressedPrefixes = kw.get('unsuppressedPrefixes')
        nsdict = kw.get('nsdict', { 'xml': XMLNS.XML, 'xmlns': XMLNS.BASE })

        # Processing state.
        self.state = (nsdict, ['xml'], [])

        if node.nodeType == Node.DOCUMENT_NODE:
            self._do_document(node)
        elif node.nodeType == Node.ELEMENT_NODE:
            self.documentOrder = _Element        # At document element
            if self.unsuppressedPrefixes is not None:
                self._do_element(node)
            else:
                inherited = self._inherit_context(node)
                self._do_element(node, inherited)
        elif node.nodeType == Node.DOCUMENT_TYPE_NODE:
            pass
        else:
            raise TypeError, str(node)


    def _inherit_context(self, node):
        '''_inherit_context(self, node) -> list
        Scan ancestors of attribute and namespace context.  Used only
        for single element node canonicalization, not for subset
        canonicalization.'''

        # Collect the initial list of xml:foo attributes.
        xmlattrs = filter(_IN_XML_NS, _attrs(node))

        # Walk up and get all xml:XXX attributes we inherit.
        inherited, parent = [], node.parentNode
        while parent and parent.nodeType == Node.ELEMENT_NODE:
            for a in filter(_IN_XML_NS, _attrs(parent)):
                n = a.localName
                if n not in xmlattrs:
                    xmlattrs.append(n)
                    inherited.append(a)
            parent = parent.parentNode
        return inherited


    def _do_document(self, node):
        '''_do_document(self, node) -> None
        Process a document node. documentOrder holds whether the document
        element has been encountered such that PIs/comments can be written
        as specified.'''

        self.documentOrder = _LesserElement
        for child in node.childNodes:
            if child.nodeType == Node.ELEMENT_NODE:
                self.documentOrder = _Element        # At document element
                self._do_element(child)
                self.documentOrder = _GreaterElement # After document element
            elif child.nodeType == Node.PROCESSING_INSTRUCTION_NODE:
                self._do_pi(child)
            elif child.nodeType == Node.COMMENT_NODE:
                self._do_comment(child)
            elif child.nodeType == Node.DOCUMENT_TYPE_NODE:
                pass
            else:
                raise TypeError, str(child)
    handlers[Node.DOCUMENT_NODE] = _do_document


    def _do_text(self, node):
        '''_do_text(self, node) -> None
        Process a text or CDATA node.  Render various special characters
        as their C14N entity representations.'''
        if not _in_subset(self.subset, node): return
        s = node.data \
                .replace("&", "&amp;") \
                .replace("<", "&lt;") \
                .replace(">", "&gt;") \
                .replace("\015", "&#xD;")
        if s: self.write(s)
    handlers[Node.TEXT_NODE] = _do_text
    handlers[Node.CDATA_SECTION_NODE] = _do_text


    def _do_pi(self, node):
        '''_do_pi(self, node) -> None
        Process a PI node. Render a leading or trailing #xA if the
        document order of the PI is greater or lesser (respectively)
        than the document element.
        '''
        if not _in_subset(self.subset, node): return
        W = self.write
        if self.documentOrder == _GreaterElement: W('\n')
        W('<?')
        W(node.nodeName)
        s = node.data
        if s:
            W(' ')
            W(s)
        W('?>')
        if self.documentOrder == _LesserElement: W('\n')
    handlers[Node.PROCESSING_INSTRUCTION_NODE] = _do_pi


    def _do_comment(self, node):
        '''_do_comment(self, node) -> None
        Process a comment node. Render a leading or trailing #xA if the
        document order of the comment is greater or lesser (respectively)
        than the document element.
        '''
        if not _in_subset(self.subset, node): return
        if self.comments:
            W = self.write
            if self.documentOrder == _GreaterElement: W('\n')
            W('<!--')
            W(node.data)
            W('-->')
            if self.documentOrder == _LesserElement: W('\n')
    handlers[Node.COMMENT_NODE] = _do_comment


    def _do_attr(self, n, value):
        ''''_do_attr(self, node) -> None
        Process an attribute.'''

        W = self.write
        W(' ')
        W(n)
        W('="')
        s = value \
            .replace("&", "&amp;") \
            .replace("<", "&lt;") \
            .replace('"', '&quot;') \
            .replace('\011', '&#x9') \
            .replace('\012', '&#xA') \
            .replace('\015', '&#xD')
        W(s)
        W('"')

    def _do_element(self, node, initial_other_attrs = []):
        '''_do_element(self, node, initial_other_attrs = []) -> None
        Process an element (and its children).'''

        # Get state (from the stack) make local copies.
        #       ns_parent -- NS declarations in parent
        #       ns_rendered -- NS nodes rendered by ancestors
        #       xml_attrs -- Attributes in XML namespace from parent
        #       ns_local -- NS declarations relevant to this element
        ns_parent, ns_rendered, xml_attrs = \
                self.state[0], self.state[1][:], self.state[2][:]
        ns_local = ns_parent.copy()

        # Divide attributes into NS, XML, and others.
        other_attrs = initial_other_attrs[:]
        in_subset = _in_subset(self.subset, node)
        for a in _attrs(node):
            if a.namespaceURI == XMLNS.BASE:
                n = a.nodeName
                if n == "xmlns:": n = "xmlns"        # DOM bug workaround
                ns_local[n] = a.nodeValue
            elif a.namespaceURI == XMLNS.XML:
                if self.unsuppressedPrefixes is None or in_subset:
                    xml_attrs.append(a)
            else:
                other_attrs.append(a)

        # Render the node
        W, name = self.write, None
        if in_subset:
            name = node.nodeName
            W('<')
            W(name)

            # Create list of NS attributes to render.
            ns_to_render = []
            for n,v in ns_local.items():
                pval = ns_parent.get(n)

                # If default namespace is XMLNS.BASE or empty, skip
                if n == "xmlns" \
                and v in [ XMLNS.BASE, '' ] and pval in [ XMLNS.BASE, '' ]:
                    continue

                # "omit namespace node with local name xml, which defines
                # the xml prefix, if its string value is
                # http://www.w3.org/XML/1998/namespace."
                if n == "xmlns:xml" \
                and v in [ 'http://www.w3.org/XML/1998/namespace' ]:
                    continue

                # If different from parent, or parent didn't render
                # and if not exclusive, or this prefix is needed or
                # not suppressed
                if (v != pval or n not in ns_rendered) \
                  and (self.unsuppressedPrefixes is None or \
                  _utilized(n, node, other_attrs, self.unsuppressedPrefixes)):
                    ns_to_render.append((n, v))

            # Sort and render the ns, marking what was rendered.
            ns_to_render.sort(_sorter_ns)
            for n,v in ns_to_render:
                self._do_attr(n, v)
                ns_rendered.append(n)

            # Add in the XML attributes (don't pass to children, since
            # we're rendering them), sort, and render.
            other_attrs.extend(xml_attrs)
            xml_attrs = []
            other_attrs.sort(_sorter)
            for a in other_attrs:
                self._do_attr(a.nodeName, a.value)
            W('>')

        # Push state, recurse, pop state.
        state, self.state = self.state, (ns_local, ns_rendered, xml_attrs)
        for c in _children(node):
            _implementation.handlers[c.nodeType](self, c)
        self.state = state

        if name: W('</%s>' % name)
    handlers[Node.ELEMENT_NODE] = _do_element


def Canonicalize(node, output=None, **kw):
    '''Canonicalize(node, output=None, **kw) -> UTF-8

    Canonicalize a DOM document/element node and all descendents.
    Return the text; if output is specified then output.write will
    be called to output the text and None will be returned
    Keyword parameters:
        nsdict: a dictionary of prefix:uri namespace entries
                assumed to exist in the surrounding context
        comments: keep comments if non-zero (default is 0)
        subset: Canonical XML subsetting resulting from XPath
                (default is [])
        unsuppressedPrefixes: do exclusive C14N, and this specifies the
                prefixes that should be inherited.
    '''
    if output:
        if _implementation2 is None:
            _implementation(node, output.write, **kw)
        else:
            apply(_implementation2, (node, output.write), kw)
    else:
        s = StringIO.StringIO()
        if _implementation2 is None:
            _implementation(node, s.write, **kw)
        else:
            apply(_implementation2, (node, s.write), kw)
        return s.getvalue()


if __name__ == '__main__': print _copyright
