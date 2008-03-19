# Copyright (c) 2003, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory (subject to receipt of
# any required approvals from the U.S. Dept. of Energy).  All rights
# reserved. 
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.

ident = "$Id: XMLSchema.py,v 1.53 2005/02/18 13:50:14 warnes Exp $"

import types, weakref, urllib, sys
from threading import RLock
from Namespaces import XMLNS
from Utility import DOM, DOMException, Collection, SplitQName
from StringIO import StringIO

def GetSchema(component):
    """convience function for finding the parent XMLSchema instance.
    """
    parent = component
    while not isinstance(parent, XMLSchema):
        parent = parent._parent()
    return parent
    
class SchemaReader:
    """A SchemaReader creates XMLSchema objects from urls and xml data.
    """
    def __init__(self, domReader=None, base_url=None):
        """domReader -- class must implement DOMAdapterInterface
           base_url -- base url string
        """
        self.__base_url = base_url
        self.__readerClass = domReader
        if not self.__readerClass:
            self.__readerClass = DOMAdapter
        self._includes = {}
        self._imports = {}

    def __setImports(self, schema):
        """Add dictionary of imports to schema instance.
           schema -- XMLSchema instance
        """
        for ns,val in schema.imports.items(): 
            if self._imports.has_key(ns):
                schema.addImportSchema(self._imports[ns])

    def __setIncludes(self, schema):
        """Add dictionary of includes to schema instance.
           schema -- XMLSchema instance
        """
        for schemaLocation, val in schema.includes.items(): 
            if self._includes.has_key(schemaLocation):
                schema.addIncludeSchema(self._imports[schemaLocation])

    def addSchemaByLocation(self, location, schema):
        """provide reader with schema document for a location.
        """
        self._includes[location] = schema

    def addSchemaByNamespace(self, schema):
        """provide reader with schema document for a targetNamespace.
        """
        self._imports[schema.targetNamespace] = schema

    def loadFromNode(self, parent, element):
        """element -- DOM node or document
           parent -- WSDLAdapter instance
        """
        reader = self.__readerClass(element)
        schema = XMLSchema(parent)
        #HACK to keep a reference
        schema.wsdl = parent
        schema.setBaseUrl(self.__base_url)
        schema.load(reader)
        return schema
        
    def loadFromStream(self, file, url=None):
        """Return an XMLSchema instance loaded from a file object.
           file -- file object
           url -- base location for resolving imports/includes.
        """
        reader = self.__readerClass()
        reader.loadDocument(file)
        schema = XMLSchema()
        if url is not None:
             schema.setBaseUrl(url)
        schema.load(reader)
        self.__setIncludes(schema)
        self.__setImports(schema)
        return schema

    def loadFromString(self, data):
        """Return an XMLSchema instance loaded from an XML string.
           data -- XML string
        """
        return self.loadFromStream(StringIO(data))

    def loadFromURL(self, url):
        """Return an XMLSchema instance loaded from the given url.
           url -- URL to dereference
        """
        reader = self.__readerClass()
        if self.__base_url:
            url = urllib.basejoin(self.__base_url,url)
        reader.loadFromURL(url)
        schema = XMLSchema()
        schema.setBaseUrl(url)
        schema.load(reader)
        self.__setIncludes(schema)
        self.__setImports(schema)
        return schema

    def loadFromFile(self, filename):
        """Return an XMLSchema instance loaded from the given file.
           filename -- name of file to open
        """
        if self.__base_url:
            filename = urllib.basejoin(self.__base_url,filename)
        file = open(filename, 'rb')
        try:
            schema = self.loadFromStream(file, filename)
        finally:
            file.close()

        return schema


class SchemaError(Exception): 
    pass

###########################
# DOM Utility Adapters 
##########################
class DOMAdapterInterface:
    def hasattr(self, attr, ns=None):
        """return true if node has attribute 
           attr -- attribute to check for
           ns -- namespace of attribute, by default None
        """
        raise NotImplementedError, 'adapter method not implemented'

    def getContentList(self, *contents):
        """returns an ordered list of child nodes
           *contents -- list of node names to return
        """
        raise NotImplementedError, 'adapter method not implemented'

    def setAttributeDictionary(self, attributes):
        """set attribute dictionary
        """
        raise NotImplementedError, 'adapter method not implemented'

    def getAttributeDictionary(self):
        """returns a dict of node's attributes
        """
        raise NotImplementedError, 'adapter method not implemented'

    def getNamespace(self, prefix):
        """returns namespace referenced by prefix.
        """
        raise NotImplementedError, 'adapter method not implemented'

    def getTagName(self):
        """returns tagName of node
        """
        raise NotImplementedError, 'adapter method not implemented'


    def getParentNode(self):
        """returns parent element in DOMAdapter or None
        """
        raise NotImplementedError, 'adapter method not implemented'

    def loadDocument(self, file):
        """load a Document from a file object
           file --
        """
        raise NotImplementedError, 'adapter method not implemented'

    def loadFromURL(self, url):
        """load a Document from an url
           url -- URL to dereference
        """
        raise NotImplementedError, 'adapter method not implemented'


class DOMAdapter(DOMAdapterInterface):
    """Adapter for ZSI.Utility.DOM
    """
    def __init__(self, node=None):
        """Reset all instance variables.
           element -- DOM document, node, or None
        """
        if hasattr(node, 'documentElement'):
            self.__node = node.documentElement
        else:
            self.__node = node
        self.__attributes = None

    def hasattr(self, attr, ns=None):
        """attr -- attribute 
           ns -- optional namespace, None means unprefixed attribute.
        """
        if not self.__attributes:
            self.setAttributeDictionary()
        if ns:
            return self.__attributes.get(ns,{}).has_key(attr)
        return self.__attributes.has_key(attr)

    def getContentList(self, *contents):
        nodes = []
        ELEMENT_NODE = self.__node.ELEMENT_NODE
        for child in DOM.getElements(self.__node, None):
            if child.nodeType == ELEMENT_NODE and\
               SplitQName(child.tagName)[1] in contents:
                nodes.append(child)
        return map(self.__class__, nodes)

    def setAttributeDictionary(self):
        self.__attributes = {}
        for v in self.__node._attrs.values():
            self.__attributes[v.nodeName] = v.nodeValue

    def getAttributeDictionary(self):
        if not self.__attributes:
            self.setAttributeDictionary()
        return self.__attributes

    def getTagName(self):
        return self.__node.tagName

    def getParentNode(self):
        if self.__node.parentNode.nodeType == self.__node.ELEMENT_NODE:
            return DOMAdapter(self.__node.parentNode)
        return None

    def getNamespace(self, prefix):
        """prefix -- deference namespace prefix in node's context.
           Ascends parent nodes until found.
        """
        namespace = None
        if prefix == 'xmlns':
            namespace = DOM.findDefaultNS(prefix, self.__node)
        else:
            try:
                namespace = DOM.findNamespaceURI(prefix, self.__node)
            except DOMException, ex:
                if prefix != 'xml':
                    raise SchemaError, '%s namespace not declared for %s'\
                        %(prefix, self.__node._get_tagName())
                namespace = XMLNS.XML
        return namespace
           
    def loadDocument(self, file):
        self.__node = DOM.loadDocument(file)
        if hasattr(self.__node, 'documentElement'):
            self.__node = self.__node.documentElement

    def loadFromURL(self, url):
        self.__node = DOM.loadFromURL(url)
        if hasattr(self.__node, 'documentElement'):
            self.__node = self.__node.documentElement

 
class XMLBase: 
    """ These class variables are for string indentation.
    """ 
    tag = None
    __indent = 0
    __rlock = RLock()

    def __str__(self):
        XMLBase.__rlock.acquire()
        XMLBase.__indent += 1
        tmp = "<" + str(self.__class__) + '>\n'
        for k,v in self.__dict__.items():
            tmp += "%s* %s = %s\n" %(XMLBase.__indent*'  ', k, v)
        XMLBase.__indent -= 1 
        XMLBase.__rlock.release()
        return tmp


"""Marker Interface:  can determine something about an instances properties by using 
        the provided convenience functions.

"""
class DefinitionMarker: 
    """marker for definitions
    """
    pass

class DeclarationMarker: 
    """marker for declarations
    """
    pass

class AttributeMarker: 
    """marker for attributes
    """
    pass

class AttributeGroupMarker: 
    """marker for attribute groups
    """
    pass

class WildCardMarker: 
    """marker for wildcards
    """
    pass

class ElementMarker: 
    """marker for wildcards
    """
    pass

class ReferenceMarker: 
    """marker for references
    """
    pass

class ModelGroupMarker: 
    """marker for model groups
    """
    pass

class AllMarker(ModelGroupMarker): 
    """marker for all model group
    """
    pass

class ChoiceMarker(ModelGroupMarker): 
    """marker for choice model group
    """
    pass

class SequenceMarker(ModelGroupMarker): 
    """marker for sequence model group
    """
    pass

class ExtensionMarker: 
    """marker for extensions
    """
    pass

class RestrictionMarker: 
    """marker for restrictions
    """
    facets = ['enumeration', 'length', 'maxExclusive', 'maxInclusive',\
        'maxLength', 'minExclusive', 'minInclusive', 'minLength',\
        'pattern', 'fractionDigits', 'totalDigits', 'whiteSpace']

class SimpleMarker: 
    """marker for simple type information
    """
    pass

class ListMarker: 
    """marker for simple type list
    """
    pass

class UnionMarker: 
    """marker for simple type Union
    """
    pass


class ComplexMarker: 
    """marker for complex type information
    """
    pass

class LocalMarker: 
    """marker for complex type information
    """
    pass


class MarkerInterface:
    def isDefinition(self):
        return isinstance(self, DefinitionMarker)

    def isDeclaration(self):
        return isinstance(self, DeclarationMarker)

    def isAttribute(self):
        return isinstance(self, AttributeMarker)

    def isAttributeGroup(self):
        return isinstance(self, AttributeGroupMarker)

    def isElement(self):
        return isinstance(self, ElementMarker)

    def isReference(self):
        return isinstance(self, ReferenceMarker)

    def isWildCard(self):
        return isinstance(self, WildCardMarker)

    def isModelGroup(self):
        return isinstance(self, ModelGroupMarker)

    def isAll(self):
        return isinstance(self, AllMarker)

    def isChoice(self):
        return isinstance(self, ChoiceMarker)

    def isSequence(self):
        return isinstance(self, SequenceMarker)

    def isExtension(self):
        return isinstance(self, ExtensionMarker)

    def isRestriction(self):
        return isinstance(self, RestrictionMarker)

    def isSimple(self):
        return isinstance(self, SimpleMarker)

    def isComplex(self):
        return isinstance(self, ComplexMarker)

    def isLocal(self):
        return isinstance(self, LocalMarker)

    def isList(self):
        return isinstance(self, ListMarker)

    def isUnion(self):
        return isinstance(self, UnionMarker)


##########################################################
# Schema Components
#########################################################
class XMLSchemaComponent(XMLBase, MarkerInterface):
    """
       class variables: 
           required -- list of required attributes
           attributes -- dict of default attribute values, including None.
               Value can be a function for runtime dependencies.
           contents -- dict of namespace keyed content lists.
               'xsd' content of xsd namespace.
           xmlns_key -- key for declared xmlns namespace.
           xmlns -- xmlns is special prefix for namespace dictionary
           xml -- special xml prefix for xml namespace.
    """
    required = []
    attributes = {}
    contents = {}
    xmlns_key = ''
    xmlns = 'xmlns'
    xml = 'xml'

    def __init__(self, parent=None):
        """parent -- parent instance
           instance variables:
               attributes -- dictionary of node's attributes
        """
        self.attributes = None
        self._parent = parent
        if self._parent:
            self._parent = weakref.ref(parent)

        if not self.__class__ == XMLSchemaComponent\
           and not (type(self.__class__.required) == type(XMLSchemaComponent.required)\
           and type(self.__class__.attributes) == type(XMLSchemaComponent.attributes)\
           and type(self.__class__.contents) == type(XMLSchemaComponent.contents)):
            raise RuntimeError, 'Bad type for a class variable in %s' %self.__class__

    def getItemTrace(self):
        """Returns a node trace up to the <schema> item.
        """
        item, path, name, ref = self, [], 'name', 'ref'
        while not isinstance(item,XMLSchema) and not isinstance(item,WSDLToolsAdapter):
            attr = item.getAttribute(name)
            if attr is None:
                attr = item.getAttribute(ref)
                if attr is None: path.append('<%s>' %(item.tag))
                else: path.append('<%s ref="%s">' %(item.tag, attr))
            else:
                path.append('<%s name="%s">' %(item.tag,attr))
            item = item._parent()
        try:
            tns = item.getTargetNamespace()
        except: 
            tns = ''
        path.append('<%s targetNamespace="%s">' %(item.tag, tns))
        path.reverse()
        return ''.join(path)

    def getTargetNamespace(self):
        """return targetNamespace
        """
        parent = self
        targetNamespace = 'targetNamespace'
        tns = self.attributes.get(targetNamespace)
        while not tns:
            parent = parent._parent()
            tns = parent.attributes.get(targetNamespace)
        return tns

    def getAttributeDeclaration(self, attribute):
        """attribute -- attribute with a QName value (eg. type).
           collection -- check types collection in parent Schema instance
        """
        return self.getQNameAttribute('attr_decl', attribute)

    def getAttributeGroup(self, attribute):
        """attribute -- attribute with a QName value (eg. type).
           collection -- check types collection in parent Schema instance
        """
        return self.getQNameAttribute('attr_groups', attribute)

    def getTypeDefinition(self, attribute):
        """attribute -- attribute with a QName value (eg. type).
           collection -- check types collection in parent Schema instance
        """
        return self.getQNameAttribute('types', attribute)

    def getElementDeclaration(self, attribute):
        """attribute -- attribute with a QName value (eg. element).
           collection -- check elements collection in parent Schema instance.
        """
        return self.getQNameAttribute('elements', attribute)

    def getModelGroup(self, attribute):
        """attribute -- attribute with a QName value (eg. ref).
           collection -- check model_group collection in parent Schema instance.
        """
        return self.getQNameAttribute('model_groups', attribute)

    def getQNameAttribute(self, collection, attribute):
        """returns object instance representing QName --> (namespace,name),
           or if does not exist return None.
           attribute -- an information item attribute, with a QName value.
           collection -- collection in parent Schema instance to search.
        """
        obj = None
        tdc = self.attributes.get(attribute)
        if tdc:
            parent = GetSchema(self)
            targetNamespace = tdc.getTargetNamespace()
            if parent.targetNamespace == targetNamespace:
                item = tdc.getName()
                try:
                    obj = getattr(parent, collection)[item]
                except KeyError, ex:
                    raise KeyError, "targetNamespace(%s) collection(%s) has no item(%s)"\
                        %(targetNamespace, collection, item)
            elif parent.imports.has_key(targetNamespace):
                schema = parent.imports[targetNamespace].getSchema()
                item = tdc.getName()
                try:
                    obj = getattr(schema, collection)[item]
                except KeyError, ex:
                    raise KeyError, "targetNamespace(%s) collection(%s) has no item(%s)"\
                        %(targetNamespace, collection, item)
        return obj

    def getXMLNS(self, prefix=None):
        """deference prefix or by default xmlns, returns namespace. 
        """
        if prefix == XMLSchemaComponent.xml:
            return XMLNS.XML
        parent = self
        ns = self.attributes[XMLSchemaComponent.xmlns].get(prefix or\
                XMLSchemaComponent.xmlns_key)
        while not ns:
            parent = parent._parent()
            ns = parent.attributes[XMLSchemaComponent.xmlns].get(prefix or\
                    XMLSchemaComponent.xmlns_key)
            if not ns and isinstance(parent, WSDLToolsAdapter):
                raise SchemaError, 'unknown prefix %s' %prefix
        return ns

    def getAttribute(self, attribute):
        """return requested attribute or None
        """
        return self.attributes.get(attribute)
 
    def setAttributes(self, node):
        """Sets up attribute dictionary, checks for required attributes and 
           sets default attribute values. attr is for default attribute values 
           determined at runtime.
           
           structure of attributes dictionary
               ['xmlns'][xmlns_key] --  xmlns namespace
               ['xmlns'][prefix] --  declared namespace prefix 
               [namespace][prefix] -- attributes declared in a namespace
               [attribute] -- attributes w/o prefix, default namespaces do
                   not directly apply to attributes, ie Name can't collide 
                   with QName.
        """
        self.attributes = {XMLSchemaComponent.xmlns:{}}
        for k,v in node.getAttributeDictionary().items():
            prefix,value = SplitQName(k)
            if value == XMLSchemaComponent.xmlns:
                self.attributes[value][prefix or XMLSchemaComponent.xmlns_key] = v
            elif prefix:
                ns = node.getNamespace(prefix)
                if not ns: 
                    raise SchemaError, 'no namespace for attribute prefix %s'\
                        %prefix
                if not self.attributes.has_key(ns):
                    self.attributes[ns] = {}
                elif self.attributes[ns].has_key(value):
                    raise SchemaError, 'attribute %s declared multiple times in %s'\
                        %(value, ns)
                self.attributes[ns][value] = v
            elif not self.attributes.has_key(value):
                self.attributes[value] = v
            else:
                raise SchemaError, 'attribute %s declared multiple times' %value

        if not isinstance(self, WSDLToolsAdapter):
            self.__checkAttributes()
        self.__setAttributeDefaults()

        #set QNames
        for k in ['type', 'element', 'base', 'ref', 'substitutionGroup', 'itemType']:
            if self.attributes.has_key(k):
                prefix, value = SplitQName(self.attributes.get(k))
                self.attributes[k] = \
                    TypeDescriptionComponent((self.getXMLNS(prefix), value))

        #Union, memberTypes is a whitespace separated list of QNames 
        for k in ['memberTypes']:
            if self.attributes.has_key(k):
                qnames = self.attributes[k]
                self.attributes[k] = []
                for qname in qnames.split():
                    prefix, value = SplitQName(qname)
                    self.attributes['memberTypes'].append(\
                        TypeDescriptionComponent(\
                            (self.getXMLNS(prefix), value)))

    def getContents(self, node):
        """retrieve xsd contents
        """
        return node.getContentList(*self.__class__.contents['xsd'])

    def __setAttributeDefaults(self):
        """Looks for default values for unset attributes.  If
           class variable representing attribute is None, then
           it must be defined as an instance variable.
        """
        for k,v in self.__class__.attributes.items():
            if v and not self.attributes.has_key(k):
                if isinstance(v, types.FunctionType):
                    self.attributes[k] = v(self)
                else:
                    self.attributes[k] = v

    def __checkAttributes(self):
        """Checks that required attributes have been defined,
           attributes w/default cannot be required.   Checks
           all defined attributes are legal, attribute 
           references are not subject to this test.
        """
        for a in self.__class__.required:
            if not self.attributes.has_key(a):
                raise SchemaError,\
                    'class instance %s, missing required attribute %s'\
                    %(self.__class__, a)
        for a in self.attributes.keys():
            if (a not in (XMLSchemaComponent.xmlns, XMLNS.XML)) and\
                (a not in self.__class__.attributes.keys()) and not\
                (self.isAttribute() and self.isReference()):
                raise SchemaError, '%s, unknown attribute(%s,%s)' \
                    %(self.getItemTrace(), a, self.attributes[a])


class WSDLToolsAdapter(XMLSchemaComponent):
    """WSDL Adapter to grab the attributes from the wsdl document node.
    """
    attributes = {'name':None, 'targetNamespace':None}
    tag = 'definitions'

    def __init__(self, wsdl):
        XMLSchemaComponent.__init__(self, parent=wsdl)
        self.setAttributes(DOMAdapter(wsdl.document))

    def getImportSchemas(self):
        """returns WSDLTools.WSDL types Collection
        """
        return self._parent().types


class Notation(XMLSchemaComponent):
    """<notation>
       parent:
           schema
       attributes:
           id -- ID
           name -- NCName, Required
           public -- token, Required
           system -- anyURI
       contents:
           annotation?
    """
    required = ['name', 'public']
    attributes = {'id':None, 'name':None, 'public':None, 'system':None}
    contents = {'xsd':('annotation')}
    tag = 'notation'

    def __init__(self, parent):
        XMLSchemaComponent.__init__(self, parent)
        self.annotation = None

    def fromDom(self, node):
        self.setAttributes(node)
        contents = self.getContents(node)

        for i in contents:
            component = SplitQName(i.getTagName())[1]
            if component == 'annotation' and not self.annotation:
                self.annotation = Annotation(self)
                self.annotation.fromDom(i)
            else:
                raise SchemaError, 'Unknown component (%s)' %(i.getTagName())


class Annotation(XMLSchemaComponent):
    """<annotation>
       parent:
           all,any,anyAttribute,attribute,attributeGroup,choice,complexContent,
           complexType,element,extension,field,group,import,include,key,keyref,
           list,notation,redefine,restriction,schema,selector,simpleContent,
           simpleType,union,unique
       attributes:
           id -- ID
       contents:
           (documentation | appinfo)*
    """
    attributes = {'id':None}
    contents = {'xsd':('documentation', 'appinfo')}
    tag = 'annotation'

    def __init__(self, parent):
        XMLSchemaComponent.__init__(self, parent)
        self.content = None

    def fromDom(self, node):
        self.setAttributes(node)
        contents = self.getContents(node)
        content = []

        for i in contents:
            component = SplitQName(i.getTagName())[1]
            if component == 'documentation':
                #print_debug('class %s, documentation skipped' %self.__class__, 5)
                continue
            elif component == 'appinfo':
                #print_debug('class %s, appinfo skipped' %self.__class__, 5)
                continue
            else:
                raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
        self.content = tuple(content)


    class Documentation(XMLSchemaComponent):
        """<documentation>
           parent:
               annotation
           attributes:
               source, anyURI
               xml:lang, language
           contents:
               mixed, any
        """
        attributes = {'source':None, 'xml:lang':None}
        contents = {'xsd':('mixed', 'any')}
        tag = 'documentation'

        def __init__(self, parent):
            XMLSchemaComponent.__init__(self, parent)
            self.content = None

        def fromDom(self, node):
            self.setAttributes(node)
            contents = self.getContents(node)
            content = []

            for i in contents:
                component = SplitQName(i.getTagName())[1]
                if component == 'mixed':
                    #print_debug('class %s, mixed skipped' %self.__class__, 5)
                    continue
                elif component == 'any':
                    #print_debug('class %s, any skipped' %self.__class__, 5)
                    continue
                else:
                    raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
            self.content = tuple(content)


    class Appinfo(XMLSchemaComponent):
        """<appinfo>
           parent:
               annotation
           attributes:
               source, anyURI
           contents:
               mixed, any
        """
        attributes = {'source':None, 'anyURI':None}
        contents = {'xsd':('mixed', 'any')}
        tag = 'appinfo'

        def __init__(self, parent):
            XMLSchemaComponent.__init__(self, parent)
            self.content = None

        def fromDom(self, node):
            self.setAttributes(node)
            contents = self.getContents(node)
            content = []

            for i in contents:
                component = SplitQName(i.getTagName())[1]
                if component == 'mixed':
                    #print_debug('class %s, mixed skipped' %self.__class__, 5)
                    continue
                elif component == 'any':
                    #print_debug('class %s, any skipped' %self.__class__, 5)
                    continue
                else:
                    raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
            self.content = tuple(content)


class XMLSchemaFake:
    # This is temporary, for the benefit of WSDL until the real thing works.
    def __init__(self, element):
        self.targetNamespace = DOM.getAttr(element, 'targetNamespace')
        self.element = element

class XMLSchema(XMLSchemaComponent):
    """A schema is a collection of schema components derived from one
       or more schema documents, that is, one or more <schema> element
       information items. It represents the abstract notion of a schema
       rather than a single schema document (or other representation).

       <schema>
       parent:
           ROOT
       attributes:
           id -- ID
           version -- token
           xml:lang -- language
           targetNamespace -- anyURI
           attributeFormDefault -- 'qualified' | 'unqualified', 'unqualified'
           elementFormDefault -- 'qualified' | 'unqualified', 'unqualified'
           blockDefault -- '#all' | list of 
               ('substitution | 'extension' | 'restriction')
           finalDefault -- '#all' | list of 
               ('extension' | 'restriction' | 'list' | 'union')
        
       contents:
           ((include | import | redefine | annotation)*, 
            (attribute, attributeGroup, complexType, element, group, 
             notation, simpleType)*, annotation*)*


        attributes -- schema attributes
        imports -- import statements
        includes -- include statements
        redefines -- 
        types    -- global simpleType, complexType definitions
        elements -- global element declarations
        attr_decl -- global attribute declarations
        attr_groups -- attribute Groups
        model_groups -- model Groups
        notations -- global notations
    """
    attributes = {'id':None, 
        'version':None, 
        'xml:lang':None, 
        'targetNamespace':None,
        'attributeFormDefault':'unqualified',
        'elementFormDefault':'unqualified',
        'blockDefault':None,
        'finalDefault':None}
    contents = {'xsd':('include', 'import', 'redefine', 'annotation', 'attribute',\
                'attributeGroup', 'complexType', 'element', 'group',\
                'notation', 'simpleType', 'annotation')}
    empty_namespace = ''
    tag = 'schema'

    def __init__(self, parent=None): 
        """parent -- 
           instance variables:
           targetNamespace -- schema's declared targetNamespace, or empty string.
           _imported_schemas -- namespace keyed dict of schema dependencies, if 
              a schema is provided instance will not resolve import statement.
           _included_schemas -- schemaLocation keyed dict of component schemas, 
              if schema is provided instance will not resolve include statement.
           _base_url -- needed for relative URLs support, only works with URLs
               relative to initial document.
           includes -- collection of include statements
           imports -- collection of import statements
           elements -- collection of global element declarations
           types -- collection of global type definitions
           attr_decl -- collection of global attribute declarations
           attr_groups -- collection of global attribute group definitions
           model_groups -- collection of model group definitions
           notations -- collection of notations

        """
        self.targetNamespace = None
        XMLSchemaComponent.__init__(self, parent)
        f = lambda k: k.attributes['name']
        ns = lambda k: k.attributes['namespace']
        sl = lambda k: k.attributes['schemaLocation']
        self.includes = Collection(self, key=sl)
        self.imports = Collection(self, key=ns)
        self.elements = Collection(self, key=f)
        self.types = Collection(self, key=f)
        self.attr_decl = Collection(self, key=f)
        self.attr_groups = Collection(self, key=f)
        self.model_groups = Collection(self, key=f)
        self.notations = Collection(self, key=f)

        self._imported_schemas = {}
        self._included_schemas = {}
        self._base_url = None

    def addImportSchema(self, schema):
        """for resolving import statements in Schema instance
           schema -- schema instance
           _imported_schemas 
        """
        if not isinstance(schema, XMLSchema):
            raise TypeError, 'expecting a Schema instance'
        if schema.targetNamespace != self.targetNamespace:
            self._imported_schemas[schema.targetNamespace] = schema
        else:
            raise SchemaError, 'import schema bad targetNamespace'

    def addIncludeSchema(self, schemaLocation, schema):
        """for resolving include statements in Schema instance
           schemaLocation -- schema location
           schema -- schema instance
           _included_schemas 
        """
        if not isinstance(schema, XMLSchema):
            raise TypeError, 'expecting a Schema instance'
        if not schema.targetNamespace or\
             schema.targetNamespace == self.targetNamespace:
            self._included_schemas[schemaLocation] = schema
        else:
            raise SchemaError, 'include schema bad targetNamespace'
        
    def setImportSchemas(self, schema_dict):
        """set the import schema dictionary, which is used to 
           reference depedent schemas.
        """
        self._imported_schemas = schema_dict

    def getImportSchemas(self):
        """get the import schema dictionary, which is used to 
           reference depedent schemas.
        """
        return self._imported_schemas

    def getSchemaNamespacesToImport(self):
        """returns tuple of namespaces the schema instance has declared
           itself to be depedent upon.
        """
        return tuple(self.includes.keys())

    def setIncludeSchemas(self, schema_dict):
        """set the include schema dictionary, which is keyed with 
           schemaLocation (uri).  
           This is a means of providing 
           schemas to the current schema for content inclusion.
        """
        self._included_schemas = schema_dict

    def getIncludeSchemas(self):
        """get the include schema dictionary, which is keyed with 
           schemaLocation (uri). 
        """
        return self._included_schemas

    def getBaseUrl(self):
        """get base url, used for normalizing all relative uri's 
        """
        return self._base_url

    def setBaseUrl(self, url):
        """set base url, used for normalizing all relative uri's 
        """
        self._base_url = url

    def getElementFormDefault(self):
        """return elementFormDefault attribute
        """
        return self.attributes.get('elementFormDefault')

    def isElementFormDefaultQualified(self):
        return self.attributes.get('elementFormDefault') == 'qualified'

    def getAttributeFormDefault(self):
        """return attributeFormDefault attribute
        """
        return self.attributes.get('attributeFormDefault')

    def getBlockDefault(self):
        """return blockDefault attribute
        """
        return self.attributes.get('blockDefault')

    def getFinalDefault(self):
        """return finalDefault attribute 
        """
        return self.attributes.get('finalDefault')

    def load(self, node):
        pnode = node.getParentNode()
        if pnode:
            pname = SplitQName(pnode.getTagName())[1]
            if pname == 'types':
                attributes = {}
                self.setAttributes(pnode)
                attributes.update(self.attributes)
                self.setAttributes(node)
                for k,v in attributes['xmlns'].items():
                    if not self.attributes['xmlns'].has_key(k):
                        self.attributes['xmlns'][k] = v
            else:
                self.setAttributes(node)
        else:
            self.setAttributes(node)

        self.targetNamespace = self.getTargetNamespace()
        contents = self.getContents(node)

        indx = 0
        num = len(contents)
        while indx < num:
            while indx < num:
                node = contents[indx]
                component = SplitQName(node.getTagName())[1]

                if component == 'include':
                    tp = self.__class__.Include(self)
                    tp.fromDom(node)
                    self.includes[tp.attributes['schemaLocation']] = tp

                    schema = tp.getSchema()
                    if schema.targetNamespace and \
                        schema.targetNamespace != self.targetNamespace:
                        raise SchemaError, 'included schema bad targetNamespace'

                    for collection in ['imports','elements','types',\
                        'attr_decl','attr_groups','model_groups','notations']:
                        for k,v in getattr(schema,collection).items():
                            if not getattr(self,collection).has_key(k):
                                v._parent = weakref.ref(self)
                                getattr(self,collection)[k] = v

                elif component == 'import':
                    tp = self.__class__.Import(self)
                    tp.fromDom(node)
                    import_ns = tp.getAttribute('namespace')
                    if import_ns:
                        if import_ns == self.targetNamespace:
                            raise SchemaError,\
                                'import and schema have same targetNamespace'
                        self.imports[import_ns] = tp
                    else:
                        self.imports[self.__class__.empty_namespace] = tp

                    if not self.getImportSchemas().has_key(import_ns) and\
                       tp.getAttribute('schemaLocation'):
                        self.addImportSchema(tp.getSchema())

                elif component == 'redefine':
                    #print_debug('class %s, redefine skipped' %self.__class__, 5)
                    pass
                elif component == 'annotation':
                    #print_debug('class %s, annotation skipped' %self.__class__, 5)
                    pass
                else:
                    break
                indx += 1

            # (attribute, attributeGroup, complexType, element, group, 
            # notation, simpleType)*, annotation*)*
            while indx < num:
                node = contents[indx]
                component = SplitQName(node.getTagName())[1]

                if component == 'attribute':
                    tp = AttributeDeclaration(self)
                    tp.fromDom(node)
                    self.attr_decl[tp.getAttribute('name')] = tp
                elif component == 'attributeGroup':
                    tp = AttributeGroupDefinition(self)
                    tp.fromDom(node)
                    self.attr_groups[tp.getAttribute('name')] = tp
                elif component == 'complexType':
                    tp = ComplexType(self)
                    tp.fromDom(node)
                    self.types[tp.getAttribute('name')] = tp
                elif component == 'element':
                    tp = ElementDeclaration(self)
                    tp.fromDom(node)
                    self.elements[tp.getAttribute('name')] = tp
                elif component == 'group':
                    tp = ModelGroupDefinition(self)
                    tp.fromDom(node)
                    self.model_groups[tp.getAttribute('name')] = tp
                elif component == 'notation':
                    tp = Notation(self)
                    tp.fromDom(node)
                    self.notations[tp.getAttribute('name')] = tp
                elif component == 'simpleType':
                    tp = SimpleType(self)
                    tp.fromDom(node)
                    self.types[tp.getAttribute('name')] = tp
                else:
                    break
                indx += 1

            while indx < num:
                node = contents[indx]
                component = SplitQName(node.getTagName())[1]

                if component == 'annotation':
                    #print_debug('class %s, annotation 2 skipped' %self.__class__, 5)
                    pass
                else:
                    break
                indx += 1


    class Import(XMLSchemaComponent):
        """<import> 
           parent:
               schema
           attributes:
               id -- ID
               namespace -- anyURI
               schemaLocation -- anyURI
           contents:
               annotation?
        """
        attributes = {'id':None,
            'namespace':None,
            'schemaLocation':None}
        contents = {'xsd':['annotation']}
        tag = 'import'

        def __init__(self, parent):
            XMLSchemaComponent.__init__(self, parent)
            self.annotation = None
            self._schema = None

        def fromDom(self, node):
            self.setAttributes(node)
            contents = self.getContents(node)

            if self.attributes['namespace'] == self.getTargetNamespace():
                raise SchemaError, 'namespace of schema and import match'

            for i in contents:
                component = SplitQName(i.getTagName())[1]
                if component == 'annotation' and not self.annotation:
                    self.annotation = Annotation(self)
                    self.annotation.fromDom(i)
                else:
                    raise SchemaError, 'Unknown component (%s)' %(i.getTagName())

        def getSchema(self):
            """if schema is not defined, first look for a Schema class instance
               in parent Schema.  Else if not defined resolve schemaLocation
               and create a new Schema class instance, and keep a hard reference. 
            """
            if not self._schema:
                ns = self.attributes['namespace']
                schema = self._parent().getImportSchemas().get(ns)
                if not schema and self._parent()._parent:
                    schema = self._parent()._parent().getImportSchemas().get(ns)
                if not schema:
                    url = self.attributes.get('schemaLocation')
                    if not url:
                        raise SchemaError, 'namespace(%s) is unknown' %ns
                    base_url = self._parent().getBaseUrl()
                    reader = SchemaReader(base_url=base_url)
                    reader._imports = self._parent().getImportSchemas()
                    reader._includes = self._parent().getIncludeSchemas()
                    self._schema = reader.loadFromURL(url)
            return self._schema or schema


    class Include(XMLSchemaComponent):
        """<include schemaLocation>
           parent:
               schema
           attributes:
               id -- ID
               schemaLocation -- anyURI, required
           contents:
               annotation?
        """
        required = ['schemaLocation']
        attributes = {'id':None,
            'schemaLocation':None}
        contents = {'xsd':['annotation']}
        tag = 'include'

        def __init__(self, parent):
            XMLSchemaComponent.__init__(self, parent)
            self.annotation = None
            self._schema = None

        def fromDom(self, node):
            self.setAttributes(node)
            contents = self.getContents(node)

            for i in contents:
                component = SplitQName(i.getTagName())[1]
                if component == 'annotation' and not self.annotation:
                    self.annotation = Annotation(self)
                    self.annotation.fromDom(i)
                else:
                    raise SchemaError, 'Unknown component (%s)' %(i.getTagName())

        def getSchema(self):
            """if schema is not defined, first look for a Schema class instance
               in parent Schema.  Else if not defined resolve schemaLocation
               and create a new Schema class instance.  
            """
            if not self._schema:
                schema = self._parent()
                self._schema = schema.getIncludeSchemas().get(\
                                   self.attributes['schemaLocation']
                                   )
                if not self._schema:
                    url = self.attributes['schemaLocation']
                    reader = SchemaReader(base_url=schema.getBaseUrl())
                    reader._imports = schema.getImportSchemas()
                    reader._includes = schema.getIncludeSchemas()
                    self._schema = reader.loadFromURL(url)
            return self._schema


class AttributeDeclaration(XMLSchemaComponent,\
                           AttributeMarker,\
                           DeclarationMarker):
    """<attribute name>
       parent: 
           schema
       attributes:
           id -- ID
           name -- NCName, required
           type -- QName
           default -- string
           fixed -- string
       contents:
           annotation?, simpleType?
    """
    required = ['name']
    attributes = {'id':None,
        'name':None,
        'type':None,
        'default':None,
        'fixed':None}
    contents = {'xsd':['annotation','simpleType']}
    tag = 'attribute'

    def __init__(self, parent):
        XMLSchemaComponent.__init__(self, parent)
        self.annotation = None
        self.content = None

    def fromDom(self, node):
        """ No list or union support
        """
        self.setAttributes(node)
        contents = self.getContents(node)

        for i in contents:
            component = SplitQName(i.getTagName())[1]
            if component == 'annotation' and not self.annotation:
                self.annotation = Annotation(self)
                self.annotation.fromDom(i)
            elif component == 'simpleType':
                self.content = AnonymousSimpleType(self)
                self.content.fromDom(i)
            else:
                raise SchemaError, 'Unknown component (%s)' %(i.getTagName())


class LocalAttributeDeclaration(AttributeDeclaration,\
                                AttributeMarker,\
                                LocalMarker,\
                                DeclarationMarker):
    """<attribute name>
       parent: 
           complexType, restriction, extension, attributeGroup
       attributes:
           id -- ID
           name -- NCName,  required
           type -- QName
           form -- ('qualified' | 'unqualified'), schema.attributeFormDefault
           use -- ('optional' | 'prohibited' | 'required'), optional
           default -- string
           fixed -- string
       contents:
           annotation?, simpleType?
    """
    required = ['name']
    attributes = {'id':None, 
        'name':None,
        'type':None,
        'form':lambda self: GetSchema(self).getAttributeFormDefault(),
        'use':'optional',
        'default':None,
        'fixed':None}
    contents = {'xsd':['annotation','simpleType']}

    def __init__(self, parent):
        AttributeDeclaration.__init__(self, parent)
        self.annotation = None
        self.content = None

    def fromDom(self, node):
        self.setAttributes(node)
        contents = self.getContents(node)

        for i in contents:
            component = SplitQName(i.getTagName())[1]
            if component == 'annotation' and not self.annotation:
                self.annotation = Annotation(self)
                self.annotation.fromDom(i)
            elif component == 'simpleType':
                self.content = AnonymousSimpleType(self)
                self.content.fromDom(i)
            else:
                raise SchemaError, 'Unknown component (%s)' %(i.getTagName())


class AttributeWildCard(XMLSchemaComponent,\
                        AttributeMarker,\
                        DeclarationMarker,\
                        WildCardMarker):
    """<anyAttribute>
       parents: 
           complexType, restriction, extension, attributeGroup
       attributes:
           id -- ID
           namespace -- '##any' | '##other' | 
                        (anyURI* | '##targetNamespace' | '##local'), ##any
           processContents -- 'lax' | 'skip' | 'strict', strict
       contents:
           annotation?
    """
    attributes = {'id':None, 
        'namespace':'##any',
        'processContents':'strict'}
    contents = {'xsd':['annotation']}
    tag = 'anyAttribute'

    def __init__(self, parent):
        XMLSchemaComponent.__init__(self, parent)
        self.annotation = None

    def fromDom(self, node):
        self.setAttributes(node)
        contents = self.getContents(node)

        for i in contents:
            component = SplitQName(i.getTagName())[1]
            if component == 'annotation' and not self.annotation:
                self.annotation = Annotation(self)
                self.annotation.fromDom(i)
            else:
                raise SchemaError, 'Unknown component (%s)' %(i.getTagName())


class AttributeReference(XMLSchemaComponent,\
                         AttributeMarker,\
                         ReferenceMarker):
    """<attribute ref>
       parents: 
           complexType, restriction, extension, attributeGroup
       attributes:
           id -- ID
           ref -- QName, required
           use -- ('optional' | 'prohibited' | 'required'), optional
           default -- string
           fixed -- string
       contents:
           annotation?
    """
    required = ['ref']
    attributes = {'id':None, 
        'ref':None,
        'use':'optional',
        'default':None,
        'fixed':None}
    contents = {'xsd':['annotation']}
    tag = 'attribute'

    def __init__(self, parent):
        XMLSchemaComponent.__init__(self, parent)
        self.annotation = None

    def getAttributeDeclaration(self, attribute='ref'):
        return XMLSchemaComponent.getAttributeDeclaration(self, attribute)

    def fromDom(self, node):
        self.setAttributes(node)
        contents = self.getContents(node)

        for i in contents:
            component = SplitQName(i.getTagName())[1]
            if component == 'annotation' and not self.annotation:
                self.annotation = Annotation(self)
                self.annotation.fromDom(i)
            else:
                raise SchemaError, 'Unknown component (%s)' %(i.getTagName())


class AttributeGroupDefinition(XMLSchemaComponent,\
                               AttributeGroupMarker,\
                               DefinitionMarker):
    """<attributeGroup name>
       parents: 
           schema, redefine
       attributes:
           id -- ID
           name -- NCName,  required
       contents:
           annotation?, (attribute | attributeGroup)*, anyAttribute?
    """
    required = ['name']
    attributes = {'id':None, 
        'name':None}
    contents = {'xsd':['annotation', 'attribute', 'attributeGroup', 'anyAttribute']}
    tag = 'attributeGroup'

    def __init__(self, parent):
        XMLSchemaComponent.__init__(self, parent)
        self.annotation = None
        self.attr_content = None

    def getAttributeContent(self):
        return self.attr_content

    def fromDom(self, node):
        self.setAttributes(node)
        contents = self.getContents(node)
        content = []

        for indx in range(len(contents)):
            component = SplitQName(contents[indx].getTagName())[1]
            if (component == 'annotation') and (not indx):
                self.annotation = Annotation(self)
                self.annotation.fromDom(contents[indx])
            elif component == 'attribute':
                if contents[indx].hasattr('name'):
                    content.append(LocalAttributeDeclaration(self))
                elif contents[indx].hasattr('ref'):
                    content.append(AttributeReference(self))
                else:
                    raise SchemaError, 'Unknown attribute type'
                content[-1].fromDom(contents[indx])
            elif component == 'attributeGroup':
                content.append(AttributeGroupReference(self))
                content[-1].fromDom(contents[indx])
            elif component == 'anyAttribute':
                if len(contents) != indx+1: 
                    raise SchemaError, 'anyAttribute is out of order in %s' %self.getItemTrace()
                content.append(AttributeWildCard(self))
                content[-1].fromDom(contents[indx])
            else:
                raise SchemaError, 'Unknown component (%s)' %(contents[indx].getTagName())

        self.attr_content = tuple(content)

class AttributeGroupReference(XMLSchemaComponent,\
                              AttributeGroupMarker,\
                              ReferenceMarker):
    """<attributeGroup ref>
       parents: 
           complexType, restriction, extension, attributeGroup
       attributes:
           id -- ID
           ref -- QName, required
       contents:
           annotation?
    """
    required = ['ref']
    attributes = {'id':None, 
        'ref':None}
    contents = {'xsd':['annotation']}
    tag = 'attributeGroup'

    def __init__(self, parent):
        XMLSchemaComponent.__init__(self, parent)
        self.annotation = None

    def getAttributeGroup(self, attribute='ref'):
        """attribute -- attribute with a QName value (eg. type).
           collection -- check types collection in parent Schema instance
        """
        return XMLSchemaComponent.getQNameAttribute(self, 'attr_groups', attribute)

    def fromDom(self, node):
        self.setAttributes(node)
        contents = self.getContents(node)

        for i in contents:
            component = SplitQName(i.getTagName())[1]
            if component == 'annotation' and not self.annotation:
                self.annotation = Annotation(self)
                self.annotation.fromDom(i)
            else:
                raise SchemaError, 'Unknown component (%s)' %(i.getTagName())



######################################################
# Elements
#####################################################
class IdentityConstrants(XMLSchemaComponent):
    """Allow one to uniquely identify nodes in a document and ensure the 
       integrity of references between them.

       attributes -- dictionary of attributes
       selector -- XPath to selected nodes
       fields -- list of XPath to key field
    """
    def __init__(self, parent):
        XMLSchemaComponent.__init__(self, parent)
        self.selector = None
        self.fields = None
        self.annotation = None

    def fromDom(self, node):
        self.setAttributes(node)
        contents = self.getContents(node)
        fields = []

        for i in contents:
            component = SplitQName(i.getTagName())[1]
            if component in self.__class__.contents['xsd']:
                if component == 'annotation' and not self.annotation:
                    self.annotation = Annotation(self)
                    self.annotation.fromDom(i)
                elif component == 'selector':
                    self.selector = self.Selector(self)
                    self.selector.fromDom(i)
                    continue
                elif component == 'field':
                    fields.append(self.Field(self))
                    fields[-1].fromDom(i)
                    continue
                else:
                    raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
            else:
                raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
            self.fields = tuple(fields)


    class Constraint(XMLSchemaComponent):
        def __init__(self, parent):
            XMLSchemaComponent.__init__(self, parent)
            self.annotation = None

        def fromDom(self, node):
            self.setAttributes(node)
            contents = self.getContents(node)

            for i in contents:
                component = SplitQName(i.getTagName())[1]
                if component in self.__class__.contents['xsd']:
                    if component == 'annotation' and not self.annotation:
                        self.annotation = Annotation(self)
                        self.annotation.fromDom(i)
                    else:
                        raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
                else:
                    raise SchemaError, 'Unknown component (%s)' %(i.getTagName())

    class Selector(Constraint):
        """<selector xpath>
           parent: 
               unique, key, keyref
           attributes:
               id -- ID
               xpath -- XPath subset,  required
           contents:
               annotation?
        """
        required = ['xpath']
        attributes = {'id':None, 
            'xpath':None}
        contents = {'xsd':['annotation']}
        tag = 'selector'

    class Field(Constraint): 
        """<field xpath>
           parent: 
               unique, key, keyref
           attributes:
               id -- ID
               xpath -- XPath subset,  required
           contents:
               annotation?
        """
        required = ['xpath']
        attributes = {'id':None, 
            'xpath':None}
        contents = {'xsd':['annotation']}
        tag = 'field'


class Unique(IdentityConstrants):
    """<unique name> Enforce fields are unique w/i a specified scope.

       parent: 
           element
       attributes:
           id -- ID
           name -- NCName,  required
       contents:
           annotation?, selector, field+
    """
    required = ['name']
    attributes = {'id':None, 
        'name':None}
    contents = {'xsd':['annotation', 'selector', 'field']}
    tag = 'unique'


class Key(IdentityConstrants):
    """<key name> Enforce fields are unique w/i a specified scope, and all
           field values are present w/i document.  Fields cannot
           be nillable.

       parent: 
           element
       attributes:
           id -- ID
           name -- NCName,  required
       contents:
           annotation?, selector, field+
    """
    required = ['name']
    attributes = {'id':None, 
        'name':None}
    contents = {'xsd':['annotation', 'selector', 'field']}
    tag = 'key'


class KeyRef(IdentityConstrants):
    """<keyref name refer> Ensure a match between two sets of values in an 
           instance.
       parent: 
           element
       attributes:
           id -- ID
           name -- NCName,  required
           refer -- QName,  required
       contents:
           annotation?, selector, field+
    """
    required = ['name', 'refer']
    attributes = {'id':None, 
        'name':None,
        'refer':None}
    contents = {'xsd':['annotation', 'selector', 'field']}
    tag = 'keyref'


class ElementDeclaration(XMLSchemaComponent,\
                         ElementMarker,\
                         DeclarationMarker):
    """<element name>
       parents:
           schema
       attributes:
           id -- ID
           name -- NCName,  required
           type -- QName
           default -- string
           fixed -- string
           nillable -- boolean,  false
           abstract -- boolean,  false
           substitutionGroup -- QName
           block -- ('#all' | ('substition' | 'extension' | 'restriction')*), 
               schema.blockDefault 
           final -- ('#all' | ('extension' | 'restriction')*), 
               schema.finalDefault 
       contents:
           annotation?, (simpleType,complexType)?, (key | keyref | unique)*
           
    """
    required = ['name']
    attributes = {'id':None, 
        'name':None,
        'type':None,
        'default':None,
        'fixed':None,
        'nillable':0,
        'abstract':0,
        'substitutionGroup':None,
        'block':lambda self: self._parent().getBlockDefault(),
        'final':lambda self: self._parent().getFinalDefault()}
    contents = {'xsd':['annotation', 'simpleType', 'complexType', 'key',\
        'keyref', 'unique']}
    tag = 'element'

    def __init__(self, parent):
        XMLSchemaComponent.__init__(self, parent)
        self.annotation = None
        self.content = None
        self.constraints = ()

    def isQualified(self):
        '''Global elements are always qualified.
        '''
        return True

    def getElementDeclaration(self, attribute):
        raise Warning, 'invalid operation for <%s>' %self.tag

    def getTypeDefinition(self, attribute=None):
        '''If attribute is None, "type" is assumed, return the corresponding
        representation of the global type definition (TypeDefinition),
        or the local definition if don't find "type".  To maintain backwards
        compat, if attribute is provided call base class method.
        '''
        if attribute:
            return XMLSchemaComponent.getTypeDefinition(self, attribute)
        gt = XMLSchemaComponent.getTypeDefinition(self, 'type')
        if gt:
            return gt
        return self.content

    def getConstraints(self):
        return self._constraints
    def setConstraints(self, constraints):
        self._constraints = tuple(constraints)
    constraints = property(getConstraints, setConstraints, None, "tuple of key, keyref, unique constraints")

    def fromDom(self, node):
        self.setAttributes(node)
        contents = self.getContents(node)
        constraints = []
        for i in contents:
            component = SplitQName(i.getTagName())[1]
            if component in self.__class__.contents['xsd']:
                if component == 'annotation' and not self.annotation:
                    self.annotation = Annotation(self)
                    self.annotation.fromDom(i)
                elif component == 'simpleType' and not self.content:
	            self.content = AnonymousSimpleType(self)
                    self.content.fromDom(i)
                elif component == 'complexType' and not self.content:
	            self.content = LocalComplexType(self)
                    self.content.fromDom(i)
                elif component == 'key':
	            constraints.append(Key(self))
	            constraints[-1].fromDom(i)
                elif component == 'keyref':
	            constraints.append(KeyRef(self))
	            constraints[-1].fromDom(i)
                elif component == 'unique':
	            constraints.append(Unique(self))
	            constraints[-1].fromDom(i)
                else:
	            raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
            else:
	        raise SchemaError, 'Unknown component (%s)' %(i.getTagName())

        self.constraints = constraints


class LocalElementDeclaration(ElementDeclaration,\
                              LocalMarker):
    """<element>
       parents:
           all, choice, sequence
       attributes:
           id -- ID
           name -- NCName,  required
           form -- ('qualified' | 'unqualified'), schema.elementFormDefault
           type -- QName
           minOccurs -- Whole Number, 1
           maxOccurs -- (Whole Number | 'unbounded'), 1
           default -- string
           fixed -- string
           nillable -- boolean,  false
           block -- ('#all' | ('extension' | 'restriction')*), schema.blockDefault 
       contents:
           annotation?, (simpleType,complexType)?, (key | keyref | unique)*
    """
    required = ['name']
    attributes = {'id':None, 
        'name':None,
        'form':lambda self: GetSchema(self).getElementFormDefault(),
        'type':None,
        'minOccurs':'1',
        'maxOccurs':'1',
        'default':None,
        'fixed':None,
        'nillable':0,
        'abstract':0,
        'block':lambda self: GetSchema(self).getBlockDefault()}
    contents = {'xsd':['annotation', 'simpleType', 'complexType', 'key',\
        'keyref', 'unique']}

    def isQualified(self):
        '''Local elements can be qualified or unqualifed according
        to the attribute form, or the elementFormDefault.  By default
        local elements are unqualified.
        '''
        form = self.getAttribute('form')
        if form == 'qualified':
            return True
        if form == 'unqualified':
            return False
	raise SchemaError, 'Bad form (%s) for element: %s' %(form, self.getItemTrace())


class ElementReference(XMLSchemaComponent,\
                       ElementMarker,\
                       ReferenceMarker):
    """<element ref>
       parents: 
           all, choice, sequence
       attributes:
           id -- ID
           ref -- QName, required
           minOccurs -- Whole Number, 1
           maxOccurs -- (Whole Number | 'unbounded'), 1
       contents:
           annotation?
    """
    required = ['ref']
    attributes = {'id':None, 
        'ref':None,
        'minOccurs':'1',
        'maxOccurs':'1'}
    contents = {'xsd':['annotation']}
    tag = 'element'

    def __init__(self, parent):
        XMLSchemaComponent.__init__(self, parent)
        self.annotation = None

    def getElementDeclaration(self, attribute=None):
        '''If attribute is None, "ref" is assumed, return the corresponding
        representation of the global element declaration (ElementDeclaration),
        To maintain backwards compat, if attribute is provided call base class method.
        '''
        if attribute:
            return XMLSchemaComponent.getElementDeclaration(self, attribute)
        return XMLSchemaComponent.getElementDeclaration(self, 'ref')
 
    def fromDom(self, node):
        self.annotation = None
        self.setAttributes(node)
        for i in self.getContents(node):
            component = SplitQName(i.getTagName())[1]
            if component in self.__class__.contents['xsd']:
                if component == 'annotation' and not self.annotation:
                    self.annotation = Annotation(self)
                    self.annotation.fromDom(i)
                else:
	            raise SchemaError, 'Unknown component (%s)' %(i.getTagName())


class ElementWildCard(LocalElementDeclaration,\
                      WildCardMarker):
    """<any>
       parents: 
           choice, sequence
       attributes:
           id -- ID
           minOccurs -- Whole Number, 1
           maxOccurs -- (Whole Number | 'unbounded'), 1
           namespace -- '##any' | '##other' | 
                        (anyURI* | '##targetNamespace' | '##local'), ##any
           processContents -- 'lax' | 'skip' | 'strict', strict
       contents:
           annotation?
    """
    required = []
    attributes = {'id':None, 
        'minOccurs':'1',
        'maxOccurs':'1',
        'namespace':'##any',
        'processContents':'strict'}
    contents = {'xsd':['annotation']}
    tag = 'any'

    def __init__(self, parent):
        XMLSchemaComponent.__init__(self, parent)
        self.annotation = None

    def isQualified(self):
        '''Global elements are always qualified, but if processContents
        are not strict could have dynamically generated local elements.
        '''
        return GetSchema(self).isElementFormDefaultQualified()

    def getTypeDefinition(self, attribute):
        raise Warning, 'invalid operation for <%s>' %self.tag

    def fromDom(self, node):
        self.annotation = None
        self.setAttributes(node)
        for i in self.getContents(node):
            component = SplitQName(i.getTagName())[1]
            if component in self.__class__.contents['xsd']:
                if component == 'annotation' and not self.annotation:
                    self.annotation = Annotation(self)
                    self.annotation.fromDom(i)
                else:
	            raise SchemaError, 'Unknown component (%s)' %(i.getTagName())


######################################################
# Model Groups
#####################################################
class Sequence(XMLSchemaComponent,\
               SequenceMarker):
    """<sequence>
       parents: 
           complexType, extension, restriction, group, choice, sequence
       attributes:
           id -- ID
           minOccurs -- Whole Number, 1
           maxOccurs -- (Whole Number | 'unbounded'), 1

       contents:
           annotation?, (element | group | choice | sequence | any)*
    """
    attributes = {'id':None, 
        'minOccurs':'1',
        'maxOccurs':'1'}
    contents = {'xsd':['annotation', 'element', 'group', 'choice', 'sequence',\
         'any']}
    tag = 'sequence'

    def __init__(self, parent):
        XMLSchemaComponent.__init__(self, parent)
        self.annotation = None
        self.content = None

    def fromDom(self, node):
        self.setAttributes(node)
        contents = self.getContents(node)
        content = []

        for i in contents:
            component = SplitQName(i.getTagName())[1]
            if component in self.__class__.contents['xsd']:
                if component == 'annotation' and not self.annotation:
                    self.annotation = Annotation(self)
                    self.annotation.fromDom(i)
                    continue
                elif component == 'element':
                    if i.hasattr('ref'):
	                content.append(ElementReference(self))
                    else:
	                content.append(LocalElementDeclaration(self))
                elif component == 'group':
	            content.append(ModelGroupReference(self))
                elif component == 'choice':
	            content.append(Choice(self))
                elif component == 'sequence':
	            content.append(Sequence(self))
                elif component == 'any':
	            content.append(ElementWildCard(self))
                else:
	            raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
                content[-1].fromDom(i)
            else:
	        raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
        self.content = tuple(content)


class All(XMLSchemaComponent,\
          AllMarker):
    """<all>
       parents: 
           complexType, extension, restriction, group
       attributes:
           id -- ID
           minOccurs -- '0' | '1', 1
           maxOccurs -- '1', 1

       contents:
           annotation?, element*
    """
    attributes = {'id':None, 
        'minOccurs':'1',
        'maxOccurs':'1'}
    contents = {'xsd':['annotation', 'element']}
    tag = 'all'

    def __init__(self, parent):
        XMLSchemaComponent.__init__(self, parent)
        self.annotation = None
        self.content = None

    def fromDom(self, node):
        self.setAttributes(node)
        contents = self.getContents(node)
        content = []

        for i in contents:
            component = SplitQName(i.getTagName())[1]
            if component in self.__class__.contents['xsd']:
                if component == 'annotation' and not self.annotation:
                    self.annotation = Annotation(self)
                    self.annotation.fromDom(i)
                    continue
                elif component == 'element':
                    if i.hasattr('ref'):
	                content.append(ElementReference(self))
                    else:
	                content.append(LocalElementDeclaration(self))
                else:
	            raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
                content[-1].fromDom(i)
            else:
	        raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
        self.content = tuple(content)


class Choice(XMLSchemaComponent,\
             ChoiceMarker):
    """<choice>
       parents: 
           complexType, extension, restriction, group, choice, sequence
       attributes:
           id -- ID
           minOccurs -- Whole Number, 1
           maxOccurs -- (Whole Number | 'unbounded'), 1

       contents:
           annotation?, (element | group | choice | sequence | any)*
    """
    attributes = {'id':None, 
        'minOccurs':'1',
        'maxOccurs':'1'}
    contents = {'xsd':['annotation', 'element', 'group', 'choice', 'sequence',\
         'any']}
    tag = 'choice'

    def __init__(self, parent):
        XMLSchemaComponent.__init__(self, parent)
        self.annotation = None
        self.content = None

    def fromDom(self, node):
        self.setAttributes(node)
        contents = self.getContents(node)
        content = []

        for i in contents:
            component = SplitQName(i.getTagName())[1]
            if component in self.__class__.contents['xsd']:
                if component == 'annotation' and not self.annotation:
                    self.annotation = Annotation(self)
                    self.annotation.fromDom(i)
                    continue
                elif component == 'element':
                    if i.hasattr('ref'):
	                content.append(ElementReference(self))
                    else:
	                content.append(LocalElementDeclaration(self))
                elif component == 'group':
	            content.append(ModelGroupReference(self))
                elif component == 'choice':
	            content.append(Choice(self))
                elif component == 'sequence':
	            content.append(Sequence(self))
                elif component == 'any':
	            content.append(ElementWildCard(self))
                else:
	            raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
                content[-1].fromDom(i)
            else:
	        raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
        self.content = tuple(content)


class ModelGroupDefinition(XMLSchemaComponent,\
                           ModelGroupMarker,\
                           DefinitionMarker):
    """<group name>
       parents:
           redefine, schema
       attributes:
           id -- ID
           name -- NCName,  required

       contents:
           annotation?, (all | choice | sequence)?
    """
    required = ['name']
    attributes = {'id':None, 
        'name':None}
    contents = {'xsd':['annotation', 'all', 'choice', 'sequence']}
    tag = 'group'

    def __init__(self, parent):
        XMLSchemaComponent.__init__(self, parent)
        self.annotation = None
        self.content = None

    def fromDom(self, node):
        self.setAttributes(node)
        contents = self.getContents(node)

        for i in contents:
            component = SplitQName(i.getTagName())[1]
            if component in self.__class__.contents['xsd']:
                if component == 'annotation' and not self.annotation:
                    self.annotation = Annotation(self)
                    self.annotation.fromDom(i)
                    continue
                elif component == 'all' and not self.content:
                    self.content = All(self)
                elif component == 'choice' and not self.content:
                    self.content = Choice(self)
                elif component == 'sequence' and not self.content:
                    self.content = Sequence(self)
                else:
	            raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
                self.content.fromDom(i)
            else:
	        raise SchemaError, 'Unknown component (%s)' %(i.getTagName())


class ModelGroupReference(XMLSchemaComponent,\
                          ModelGroupMarker,\
                          ReferenceMarker):
    """<group ref>
       parents:
           choice, complexType, extension, restriction, sequence
       attributes:
           id -- ID
           ref -- NCName,  required
           minOccurs -- Whole Number, 1
           maxOccurs -- (Whole Number | 'unbounded'), 1

       contents:
           annotation?
    """
    required = ['ref']
    attributes = {'id':None, 
        'ref':None,
        'minOccurs':'1',
        'maxOccurs':'1'}
    contents = {'xsd':['annotation']}
    tag = 'group'

    def __init__(self, parent):
        XMLSchemaComponent.__init__(self, parent)
        self.annotation = None

    def getModelGroupReference(self):
        return self.getModelGroup('ref')

    def fromDom(self, node):
        self.setAttributes(node)
        contents = self.getContents(node)

        for i in contents:
            component = SplitQName(i.getTagName())[1]
            if component in self.__class__.contents['xsd']:
                if component == 'annotation' and not self.annotation:
                    self.annotation = Annotation(self)
                    self.annotation.fromDom(i)
                else:
	            raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
            else:
	        raise SchemaError, 'Unknown component (%s)' %(i.getTagName())



class ComplexType(XMLSchemaComponent,\
                  DefinitionMarker,\
                  ComplexMarker):
    """<complexType name>
       parents:
           redefine, schema
       attributes:
           id -- ID
           name -- NCName,  required
           mixed -- boolean, false
           abstract -- boolean,  false
           block -- ('#all' | ('extension' | 'restriction')*), schema.blockDefault 
           final -- ('#all' | ('extension' | 'restriction')*), schema.finalDefault 

       contents:
           annotation?, (simpleContent | complexContent | 
           ((group | all | choice | sequence)?, (attribute | attributeGroup)*, anyAttribute?))
    """
    required = ['name']
    attributes = {'id':None, 
        'name':None,
        'mixed':0,
        'abstract':0,
        'block':lambda self: self._parent().getBlockDefault(),
        'final':lambda self: self._parent().getFinalDefault()}
    contents = {'xsd':['annotation', 'simpleContent', 'complexContent',\
        'group', 'all', 'choice', 'sequence', 'attribute', 'attributeGroup',\
        'anyAttribute', 'any']}
    tag = 'complexType'

    def __init__(self, parent):
        XMLSchemaComponent.__init__(self, parent)
        self.annotation = None
        self.content = None
        self.attr_content = None

    def getAttributeContent(self):
        return self.attr_content

    def getElementDeclaration(self, attribute):
        raise Warning, 'invalid operation for <%s>' %self.tag

    def getTypeDefinition(self, attribute):
        raise Warning, 'invalid operation for <%s>' %self.tag

    def fromDom(self, node):
        self.setAttributes(node)
        contents = self.getContents(node)
      
        indx = 0
        num = len(contents)
        #XXX ugly
        if not num:
            return
        component = SplitQName(contents[indx].getTagName())[1]
        if component == 'annotation':
            self.annotation = Annotation(self)
            self.annotation.fromDom(contents[indx])
            indx += 1
            component = SplitQName(contents[indx].getTagName())[1]

        self.content = None
        if component == 'simpleContent':
            self.content = self.__class__.SimpleContent(self)
            self.content.fromDom(contents[indx])
        elif component == 'complexContent':
            self.content = self.__class__.ComplexContent(self)
            self.content.fromDom(contents[indx])
        else:
            if component == 'all':
                self.content = All(self)
            elif component == 'choice':
                self.content = Choice(self)
            elif component == 'sequence':
                self.content = Sequence(self)
            elif component == 'group':
                self.content = ModelGroupReference(self)

            if self.content:
                self.content.fromDom(contents[indx])
                indx += 1

            self.attr_content = []
            while indx < num:
                component = SplitQName(contents[indx].getTagName())[1]
                if component == 'attribute':
                    if contents[indx].hasattr('ref'):
                        self.attr_content.append(AttributeReference(self))
                    else:
                        self.attr_content.append(LocalAttributeDeclaration(self))
                elif component == 'attributeGroup':
                    self.attr_content.append(AttributeGroupReference(self))
                elif component == 'anyAttribute':
                    self.attr_content.append(AttributeWildCard(self))
                else:
	            raise SchemaError, 'Unknown component (%s): %s' \
                        %(contents[indx].getTagName(),self.getItemTrace())
                self.attr_content[-1].fromDom(contents[indx])
                indx += 1

    class _DerivedType(XMLSchemaComponent):
	def __init__(self, parent):
            XMLSchemaComponent.__init__(self, parent)
            self.annotation = None
            self.derivation = None

        def fromDom(self, node):
            self.setAttributes(node)
            contents = self.getContents(node)

            for i in contents:
                component = SplitQName(i.getTagName())[1]
                if component in self.__class__.contents['xsd']:
                    if component == 'annotation' and not self.annotation:
                        self.annotation = Annotation(self)
                        self.annotation.fromDom(i)
                        continue
                    elif component == 'restriction' and not self.derivation:
                        self.derivation = self.__class__.Restriction(self)
                    elif component == 'extension' and not self.derivation:
                        self.derivation = self.__class__.Extension(self)
                    else:
	                raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
                else:
	            raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
                self.derivation.fromDom(i)

    class ComplexContent(_DerivedType,\
                         ComplexMarker):
        """<complexContent>
           parents:
               complexType
           attributes:
               id -- ID
               mixed -- boolean, false

           contents:
               annotation?, (restriction | extension)
        """
        attributes = {'id':None, 
            'mixed':0 }
        contents = {'xsd':['annotation', 'restriction', 'extension']}
        tag = 'complexContent'

        class _DerivationBase(XMLSchemaComponent):
            """<extension>,<restriction>
               parents:
                   complexContent
               attributes:
                   id -- ID
                   base -- QName, required

               contents:
                   annotation?, (group | all | choice | sequence)?, 
                       (attribute | attributeGroup)*, anyAttribute?
            """
            required = ['base']
            attributes = {'id':None, 
                'base':None }
            contents = {'xsd':['annotation', 'group', 'all', 'choice',\
                'sequence', 'attribute', 'attributeGroup', 'anyAttribute']}

            def __init__(self, parent):
                XMLSchemaComponent.__init__(self, parent)
                self.annotation = None
                self.content = None
                self.attr_content = None

            def getAttributeContent(self):
                return self.attr_content

            def fromDom(self, node):
                self.setAttributes(node)
                contents = self.getContents(node)

                indx = 0
                num = len(contents)
                #XXX ugly
                if not num:
                    return
                component = SplitQName(contents[indx].getTagName())[1]
                if component == 'annotation':
                    self.annotation = Annotation(self)
                    self.annotation.fromDom(contents[indx])
                    indx += 1
                    component = SplitQName(contents[indx].getTagName())[1]

                if component == 'all':
                    self.content = All(self)
                    self.content.fromDom(contents[indx])
                    indx += 1
                elif component == 'choice':
                    self.content = Choice(self)
                    self.content.fromDom(contents[indx])
                    indx += 1
                elif component == 'sequence':
                    self.content = Sequence(self)
                    self.content.fromDom(contents[indx])
                    indx += 1
                elif component == 'group':
                    self.content = ModelGroupReference(self)
                    self.content.fromDom(contents[indx])
                    indx += 1
                else:
	            self.content = None

                self.attr_content = []
                while indx < num:
                    component = SplitQName(contents[indx].getTagName())[1]
                    if component == 'attribute':
                        if contents[indx].hasattr('ref'):
                            self.attr_content.append(AttributeReference(self))
                        else:
                            self.attr_content.append(LocalAttributeDeclaration(self))
                    elif component == 'attributeGroup':
                        if contents[indx].hasattr('ref'):
                            self.attr_content.append(AttributeGroupReference(self))
                        else:
                            self.attr_content.append(AttributeGroupDefinition(self))
                    elif component == 'anyAttribute':
                        self.attr_content.append(AttributeWildCard(self))
                    else:
	                raise SchemaError, 'Unknown component (%s)' %(contents[indx].getTagName())
                    self.attr_content[-1].fromDom(contents[indx])
                    indx += 1

        class Extension(_DerivationBase, 
                        ExtensionMarker):
            """<extension base>
               parents:
                   complexContent
               attributes:
                   id -- ID
                   base -- QName, required

               contents:
                   annotation?, (group | all | choice | sequence)?, 
                       (attribute | attributeGroup)*, anyAttribute?
            """
            tag = 'extension'

        class Restriction(_DerivationBase,\
                          RestrictionMarker):
            """<restriction base>
               parents:
                   complexContent
               attributes:
                   id -- ID
                   base -- QName, required

               contents:
                   annotation?, (group | all | choice | sequence)?, 
                       (attribute | attributeGroup)*, anyAttribute?
            """
            tag = 'restriction'


    class SimpleContent(_DerivedType,\
                        SimpleMarker):
        """<simpleContent>
           parents:
               complexType
           attributes:
               id -- ID

           contents:
               annotation?, (restriction | extension)
        """
        attributes = {'id':None}
        contents = {'xsd':['annotation', 'restriction', 'extension']}
        tag = 'simpleContent'

        class Extension(XMLSchemaComponent,\
                        ExtensionMarker):
            """<extension base>
               parents:
                   simpleContent
               attributes:
                   id -- ID
                   base -- QName, required

               contents:
                   annotation?, (attribute | attributeGroup)*, anyAttribute?
            """
            required = ['base']
            attributes = {'id':None, 
                'base':None }
            contents = {'xsd':['annotation', 'attribute', 'attributeGroup', 
                'anyAttribute']}
            tag = 'extension'

	    def __init__(self, parent):
                XMLSchemaComponent.__init__(self, parent)
                self.annotation = None
                self.attr_content = None
 
            def getAttributeContent(self):
                return self.attr_content

            def fromDom(self, node):
                self.setAttributes(node)
                contents = self.getContents(node)

                indx = 0
                num = len(contents)

                if num:
                    component = SplitQName(contents[indx].getTagName())[1]
                    if component == 'annotation':
                        self.annotation = Annotation(self)
                        self.annotation.fromDom(contents[indx])
                        indx += 1
                        component = SplitQName(contents[indx].getTagName())[1]
    
                content = []
                while indx < num:
                    component = SplitQName(contents[indx].getTagName())[1]
                    if component == 'attribute':
                        if contents[indx].hasattr('ref'):
                            content.append(AttributeReference(self))
                        else:
                            content.append(LocalAttributeDeclaration(self))
                    elif component == 'attributeGroup':
                        content.append(AttributeGroupReference(self))
                    elif component == 'anyAttribute':
                        content.append(AttributeWildCard(self))
                    else:
	                raise SchemaError, 'Unknown component (%s)'\
                            %(contents[indx].getTagName())
                    content[-1].fromDom(contents[indx])
                    indx += 1
                self.attr_content = tuple(content)


        class Restriction(XMLSchemaComponent,\
                          RestrictionMarker):
            """<restriction base>
               parents:
                   simpleContent
               attributes:
                   id -- ID
                   base -- QName, required

               contents:
                   annotation?, simpleType?, (enumeration | length | 
                   maxExclusive | maxInclusive | maxLength | minExclusive | 
                   minInclusive | minLength | pattern | fractionDigits | 
                   totalDigits | whiteSpace)*, (attribute | attributeGroup)*, 
                   anyAttribute?
            """
            required = ['base']
            attributes = {'id':None, 
                'base':None }
            contents = {'xsd':['annotation', 'simpleType', 'attribute',\
                'attributeGroup', 'anyAttribute'] + RestrictionMarker.facets}
            tag = 'restriction'

	    def __init__(self, parent):
                XMLSchemaComponent.__init__(self, parent)
                self.annotation = None
                self.content = None
                self.attr_content = None
 
            def getAttributeContent(self):
                return self.attr_content

            def fromDom(self, node):
                self.content = []
                self.setAttributes(node)
                contents = self.getContents(node)

                indx = 0
                num = len(contents)
                component = SplitQName(contents[indx].getTagName())[1]
                if component == 'annotation':
                    self.annotation = Annotation(self)
                    self.annotation.fromDom(contents[indx])
                    indx += 1
                    component = SplitQName(contents[indx].getTagName())[1]

                content = []
                while indx < num:
                    component = SplitQName(contents[indx].getTagName())[1]
                    if component == 'attribute':
                        if contents[indx].hasattr('ref'):
                            content.append(AttributeReference(self))
                        else:
                            content.append(LocalAttributeDeclaration(self))
                    elif component == 'attributeGroup':
                        content.append(AttributeGroupReference(self))
                    elif component == 'anyAttribute':
                        content.append(AttributeWildCard(self))
                    elif component == 'simpleType':
                        self.content.append(LocalSimpleType(self))
                        self.content[-1].fromDom(contents[indx])
                    else:
	                raise SchemaError, 'Unknown component (%s)'\
                            %(contents[indx].getTagName())
                    content[-1].fromDom(contents[indx])
                    indx += 1
                self.attr_content = tuple(content)


class LocalComplexType(ComplexType,\
                       LocalMarker):
    """<complexType>
       parents:
           element
       attributes:
           id -- ID
           mixed -- boolean, false

       contents:
           annotation?, (simpleContent | complexContent | 
           ((group | all | choice | sequence)?, (attribute | attributeGroup)*, anyAttribute?))
    """
    required = []
    attributes = {'id':None, 
        'mixed':0}
    tag = 'complexType'
    

class SimpleType(XMLSchemaComponent,\
                 DefinitionMarker,\
                 SimpleMarker):
    """<simpleType name>
       parents:
           redefine, schema
       attributes:
           id -- ID
           name -- NCName, required
           final -- ('#all' | ('extension' | 'restriction' | 'list' | 'union')*), 
               schema.finalDefault 

       contents:
           annotation?, (restriction | list | union)
    """
    required = ['name']
    attributes = {'id':None,
        'name':None,
        'final':lambda self: self._parent().getFinalDefault()}
    contents = {'xsd':['annotation', 'restriction', 'list', 'union']}
    tag = 'simpleType'

    def __init__(self, parent):
        XMLSchemaComponent.__init__(self, parent)
        self.annotation = None
        self.content = None

    def getElementDeclaration(self, attribute):
        raise Warning, 'invalid operation for <%s>' %self.tag

    def getTypeDefinition(self, attribute):
        raise Warning, 'invalid operation for <%s>' %self.tag

    def fromDom(self, node):
        self.setAttributes(node)
        contents = self.getContents(node)
        for child in contents:
            component = SplitQName(child.getTagName())[1]
            if component == 'annotation':
                self.annotation = Annotation(self)
                self.annotation.fromDom(child)
                continue
            break
        else:
            return
        if component == 'restriction':
            self.content = self.__class__.Restriction(self)
        elif component == 'list':
            self.content = self.__class__.List(self)
        elif component == 'union':
            self.content = self.__class__.Union(self)
        else:
            raise SchemaError, 'Unknown component (%s)' %(component)
        self.content.fromDom(child)

    class Restriction(XMLSchemaComponent,\
                      RestrictionMarker):
        """<restriction base>
           parents:
               simpleType
           attributes:
               id -- ID
               base -- QName, required or simpleType child

           contents:
               annotation?, simpleType?, (enumeration | length | 
               maxExclusive | maxInclusive | maxLength | minExclusive | 
               minInclusive | minLength | pattern | fractionDigits | 
               totalDigits | whiteSpace)*
        """
        attributes = {'id':None, 
            'base':None }
        contents = {'xsd':['annotation', 'simpleType']+RestrictionMarker.facets}
        tag = 'restriction'

        def __init__(self, parent):
            XMLSchemaComponent.__init__(self, parent)
            self.annotation = None
            self.content = None

        def getSimpleTypeContent(self):
            for el in self.content:
                if el.isSimple(): return el
            return None

        def fromDom(self, node):
            self.setAttributes(node)
            contents = self.getContents(node)
            content = []

            for indx in range(len(contents)):
                component = SplitQName(contents[indx].getTagName())[1]
                if (component == 'annotation') and (not indx):
                    self.annotation = Annotation(self)
                    self.annotation.fromDom(contents[indx])
                    continue
                elif (component == 'simpleType') and (not indx or indx == 1):
                    content.append(AnonymousSimpleType(self))
                    content[-1].fromDom(contents[indx])
                elif component in RestrictionMarker.facets:
                    #print_debug('%s class instance, skipping %s' %(self.__class__, component))
                    pass
                else:
                    raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
            self.content = tuple(content)


    class Union(XMLSchemaComponent,
                UnionMarker):
        """<union>
           parents:
               simpleType
           attributes:
               id -- ID
               memberTypes -- list of QNames, required or simpleType child.

           contents:
               annotation?, simpleType*
        """
        attributes = {'id':None, 
            'memberTypes':None }
        contents = {'xsd':['annotation', 'simpleType']}
        tag = 'union'

        def __init__(self, parent):
            XMLSchemaComponent.__init__(self, parent)
            self.annotation = None
            self.content = None

        def fromDom(self, node):
            self.setAttributes(node)
            contents = self.getContents(node)
            content = []

            for indx in range(len(contents)):
                component = SplitQName(contents[indx].getTagName())[1]
                if (component == 'annotation') and (not indx):
                    self.annotation = Annotation(self)
                    self.annotation.fromDom(contents[indx])
                elif (component == 'simpleType'):
                    content.append(AnonymousSimpleType(self))
                    content[-1].fromDom(contents[indx])
                else:
                    raise SchemaError, 'Unknown component (%s)' %(i.getTagName())
            self.content = tuple(content)

    class List(XMLSchemaComponent, 
               ListMarker):
        """<list>
           parents:
               simpleType
           attributes:
               id -- ID
               itemType -- QName, required or simpleType child.

           contents:
               annotation?, simpleType?
        """
        attributes = {'id':None, 
            'itemType':None }
        contents = {'xsd':['annotation', 'simpleType']}
        tag = 'list'

        def __init__(self, parent):
            XMLSchemaComponent.__init__(self, parent)
            self.annotation = None
            self.content = None

        def getItemType(self):
            return self.attributes.get('itemType')

        def getTypeDefinition(self, attribute='itemType'):
            '''return the type refered to by itemType attribute or
            the simpleType content.  If returns None, then the 
            type refered to by itemType is primitive.
            '''
            tp = XMLSchemaComponent.getTypeDefinition(self, attribute)
            return tp or self.content

        def fromDom(self, node):
            self.annotation = None
            self.content = None
            self.setAttributes(node)
            contents = self.getContents(node)
            for indx in range(len(contents)):
                component = SplitQName(contents[indx].getTagName())[1]
                if (component == 'annotation') and (not indx):
                    self.annotation = Annotation(self)
                    self.annotation.fromDom(contents[indx])
                elif (component == 'simpleType'):
                    self.content = AnonymousSimpleType(self)
                    self.content.fromDom(contents[indx])
                    break
                else:
                    raise SchemaError, 'Unknown component (%s)' %(i.getTagName())

                 
class AnonymousSimpleType(SimpleType,\
                          SimpleMarker):
    """<simpleType>
       parents:
           attribute, element, list, restriction, union
       attributes:
           id -- ID

       contents:
           annotation?, (restriction | list | union)
    """
    required = []
    attributes = {'id':None}
    tag = 'simpleType'


class Redefine:
    """<redefine>
       parents:
       attributes:

       contents:
    """
    tag = 'redefine'


###########################
###########################


if sys.version_info[:2] >= (2, 2):
    tupleClass = tuple
else:
    import UserTuple
    tupleClass = UserTuple.UserTuple

class TypeDescriptionComponent(tupleClass):
    """Tuple of length 2, consisting of
       a namespace and unprefixed name.
    """
    def __init__(self, args):
        """args -- (namespace, name)
           Remove the name's prefix, irrelevant.
        """
        if len(args) != 2:
            raise TypeError, 'expecting tuple (namespace, name), got %s' %args
        elif args[1].find(':') >= 0:
            args = (args[0], SplitQName(args[1])[1])
        tuple.__init__(self, args)
        return

    def getTargetNamespace(self):
        return self[0]

    def getName(self):
        return self[1]

