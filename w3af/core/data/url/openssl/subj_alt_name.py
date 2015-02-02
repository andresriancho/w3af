"""
NDG HTTPS Client package

Use pyasn1 to provide support for parsing ASN.1 formatted subjectAltName
content for SSL peer verification.  Code based on:

http://stackoverflow.com/questions/5519958/how-do-i-parse-subjectaltname-extension-data-using-pyasn1
"""
__author__ = "P J Kershaw"
__date__ = "01/02/12"
__copyright__ = "(C) 2012 Science and Technology Facilities Council"
__license__ = "BSD - see LICENSE file in top-level directory"
__contact__ = "Philip.Kershaw@stfc.ac.uk"
__revision__ = '$Id$'

from pyasn1.type import univ, constraint, char, namedtype, tag


class DirectoryString(univ.Choice):
    """ASN.1 Directory string class"""
    componentType = namedtype.NamedTypes(
        namedtype.NamedType(
            'teletexString', char.TeletexString()),
        namedtype.NamedType(
            'printableString', char.PrintableString()),
        namedtype.NamedType(
            'universalString', char.UniversalString()),
        namedtype.NamedType(
            'utf8String', char.UTF8String()),
        namedtype.NamedType(
            'bmpString', char.BMPString()),
        namedtype.NamedType(
            'ia5String', char.IA5String()),
        )


class AttributeValue(DirectoryString):
    """ASN.1 Attribute value"""


class AttributeType(univ.ObjectIdentifier):
    """ASN.1 Attribute type"""


class AttributeTypeAndValue(univ.Sequence):
    """ASN.1 Attribute type and value class"""
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('type', AttributeType()),
        namedtype.NamedType('value', AttributeValue()),
        )


class RelativeDistinguishedName(univ.SetOf):
    """ASN.1 Realtive distinguished name"""
    componentType = AttributeTypeAndValue()

class RDNSequence(univ.SequenceOf):
    """ASN.1 RDN sequence class"""
    componentType = RelativeDistinguishedName()


class Name(univ.Choice):
    """ASN.1 name class"""
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('', RDNSequence()),
        )


class Extension(univ.Sequence):
    """ASN.1 extension class"""
    componentType = namedtype.NamedTypes(
        namedtype.NamedType('extnID', univ.ObjectIdentifier()),
        namedtype.DefaultedNamedType('critical', univ.Boolean('False')),
        namedtype.NamedType('extnValue', univ.OctetString()),
        )


class Extensions(univ.SequenceOf):
    """ASN.1 extensions class"""
    componentType = Extension()
    sizeSpec = univ.SequenceOf.sizeSpec


class GeneralName(univ.Choice):
    """ASN.1 configuration for X.509 certificate subjectAltNames fields"""
    componentType = namedtype.NamedTypes(
#        namedtype.NamedType('otherName', AnotherName().subtype(
#                            implicitTag=tag.Tag(tag.tagClassContext,
#                                                tag.tagFormatSimple, 0))),
        namedtype.NamedType('rfc822Name', char.IA5String().subtype(
                            implicitTag=tag.Tag(tag.tagClassContext,
                                                tag.tagFormatSimple, 1))),
        namedtype.NamedType('dNSName', char.IA5String().subtype(
                            implicitTag=tag.Tag(tag.tagClassContext,
                                                tag.tagFormatSimple, 2))),
#        namedtype.NamedType('x400Address', ORAddress().subtype(
#                            implicitTag=tag.Tag(tag.tagClassContext,
#                                                tag.tagFormatSimple, 3))),
        namedtype.NamedType('directoryName', Name().subtype(
                            implicitTag=tag.Tag(tag.tagClassContext,
                                                tag.tagFormatSimple, 4))),
#        namedtype.NamedType('ediPartyName', EDIPartyName().subtype(
#                            implicitTag=tag.Tag(tag.tagClassContext,
#                                                tag.tagFormatSimple, 5))),
        namedtype.NamedType('uniformResourceIdentifier', char.IA5String().\
                            subtype(implicitTag=tag.Tag(tag.tagClassContext,
                                    tag.tagFormatSimple, 6))),
        namedtype.NamedType('iPAddress', univ.OctetString().subtype(
                            implicitTag=tag.Tag(tag.tagClassContext,
                                                tag.tagFormatSimple, 7))),
        namedtype.NamedType('registeredID', univ.ObjectIdentifier().subtype(
                            implicitTag=tag.Tag(tag.tagClassContext,
                                                tag.tagFormatSimple, 8))),
        )


class GeneralNames(univ.SequenceOf):
    """Sequence of names for ASN.1 subjectAltNames settings"""
    componentType = GeneralName()
    sizeSpec = univ.SequenceOf.sizeSpec


class SubjectAltName(GeneralNames):
    """ASN.1 implementation for subjectAltNames support"""
# no-check-code
