# Copyright (C) Jean-Paul Calderone 2008, All rights reserved

"""
Unit tests for L{OpenSSL.crypto}.
"""

from unittest import TestCase

from OpenSSL.crypto import TYPE_RSA, TYPE_DSA, Error, PKey, PKeyType
from OpenSSL.crypto import X509, X509Type, X509Name, X509NameType
from OpenSSL.crypto import X509Req, X509ReqType
from OpenSSL.crypto import FILETYPE_PEM, load_certificate

class _Python23TestCaseHelper:
    # Python 2.3 compatibility.
    def assertTrue(self, *a, **kw):
        return self.failUnless(*a, **kw)


    def assertFalse(self, *a, **kw):
        return self.failIf(*a, **kw)



class PKeyTests(TestCase, _Python23TestCaseHelper):
    """
    Unit tests for L{OpenSSL.crypto.PKey}.
    """
    def test_construction(self):
        """
        L{PKey} takes no arguments and returns a new L{PKeyType} instance.
        """
        self.assertRaises(TypeError, PKey, None)
        key = PKey()
        self.assertTrue(
            isinstance(key, PKeyType),
            "%r is of type %r, should be %r" % (key, type(key), PKeyType))


    def test_pregeneration(self):
        """
        L{PKeyType.bits} and L{PKeyType.type} return C{0} before the key is
        generated.
        """
        key = PKey()
        self.assertEqual(key.type(), 0)
        self.assertEqual(key.bits(), 0)


    def test_failedGeneration(self):
        """
        L{PKeyType.generate_key} takes two arguments, the first giving the key
        type as one of L{TYPE_RSA} or L{TYPE_DSA} and the second giving the
        number of bits to generate.  If an invalid type is specified or
        generation fails, L{Error} is raised.  If an invalid number of bits is
        specified, L{ValueError} or L{Error} is raised.
        """
        key = PKey()
        self.assertRaises(TypeError, key.generate_key)
        self.assertRaises(TypeError, key.generate_key, 1, 2, 3)
        self.assertRaises(TypeError, key.generate_key, "foo", "bar")
        self.assertRaises(Error, key.generate_key, -1, 0)

        self.assertRaises(ValueError, key.generate_key, TYPE_RSA, -1)
        self.assertRaises(ValueError, key.generate_key, TYPE_RSA, 0)

        # XXX RSA generation for small values of bits is fairly buggy in a wide
        # range of OpenSSL versions.  I need to figure out what the safe lower
        # bound for a reasonable number of OpenSSL versions is and explicitly
        # check for that in the wrapper.  The failure behavior is typically an
        # infinite loop inside OpenSSL.

        # self.assertRaises(Error, key.generate_key, TYPE_RSA, 2)

        # XXX DSA generation seems happy with any number of bits.  The DSS
        # says bits must be between 512 and 1024 inclusive.  OpenSSL's DSA
        # generator doesn't seem to care about the upper limit at all.  For
        # the lower limit, it uses 512 if anything smaller is specified.
        # So, it doesn't seem possible to make generate_key fail for
        # TYPE_DSA with a bits argument which is at least an int.

        # self.assertRaises(Error, key.generate_key, TYPE_DSA, -7)


    def test_rsaGeneration(self):
        """
        L{PKeyType.generate_key} generates an RSA key when passed
        L{TYPE_RSA} as a type and a reasonable number of bits.
        """
        bits = 128
        key = PKey()
        key.generate_key(TYPE_RSA, bits)
        self.assertEqual(key.type(), TYPE_RSA)
        self.assertEqual(key.bits(), bits)


    def test_dsaGeneration(self):
        """
        L{PKeyType.generate_key} generates a DSA key when passed
        L{TYPE_DSA} as a type and a reasonable number of bits.
        """
        # 512 is a magic number.  The DSS (Digital Signature Standard)
        # allows a minimum of 512 bits for DSA.  DSA_generate_parameters
        # will silently promote any value below 512 to 512.
        bits = 512
        key = PKey()
        key.generate_key(TYPE_DSA, bits)
        self.assertEqual(key.type(), TYPE_DSA)
        self.assertEqual(key.bits(), bits)


    def test_regeneration(self):
        """
        L{PKeyType.generate_key} can be called multiple times on the same
        key to generate new keys.
        """
        key = PKey()
        for type, bits in [(TYPE_RSA, 512), (TYPE_DSA, 576)]:
             key.generate_key(type, bits)
             self.assertEqual(key.type(), type)
             self.assertEqual(key.bits(), bits)



class X509NameTests(TestCase, _Python23TestCaseHelper):
    """
    Unit tests for L{OpenSSL.crypto.X509Name}.
    """
    def _x509name(self, **attrs):
        # XXX There's no other way to get a new X509Name yet.
        name = X509().get_subject()
        attrs = attrs.items()
        # Make the order stable - order matters!
        attrs.sort(lambda (k1, v1), (k2, v2): cmp(v1, v2))
        for k, v in attrs:
            setattr(name, k, v)
        return name


    def test_attributes(self):
        """
        L{X509NameType} instances have attributes for each standard (?)
        X509Name field.
        """
        name = self._x509name()
        name.commonName = "foo"
        self.assertEqual(name.commonName, "foo")
        self.assertEqual(name.CN, "foo")
        name.CN = "baz"
        self.assertEqual(name.commonName, "baz")
        self.assertEqual(name.CN, "baz")
        name.commonName = "bar"
        self.assertEqual(name.commonName, "bar")
        self.assertEqual(name.CN, "bar")
        name.CN = "quux"
        self.assertEqual(name.commonName, "quux")
        self.assertEqual(name.CN, "quux")


    def test_copy(self):
        """
        L{X509Name} creates a new L{X509NameType} instance with all the same
        attributes as an existing L{X509NameType} instance when called with
        one.
        """
        name = self._x509name(commonName="foo", emailAddress="bar@example.com")

        copy = X509Name(name)
        self.assertEqual(copy.commonName, "foo")
        self.assertEqual(copy.emailAddress, "bar@example.com")

        # Mutate the copy and ensure the original is unmodified.
        copy.commonName = "baz"
        self.assertEqual(name.commonName, "foo")

        # Mutate the original and ensure the copy is unmodified.
        name.emailAddress = "quux@example.com"
        self.assertEqual(copy.emailAddress, "bar@example.com")


    def test_repr(self):
        """
        L{repr} passed an L{X509NameType} instance should return a string
        containing a description of the type and the NIDs which have been set
        on it.
        """
        name = self._x509name(commonName="foo", emailAddress="bar")
        self.assertEqual(
            repr(name),
            "<X509Name object '/emailAddress=bar/CN=foo'>")


    def test_comparison(self):
        """
        L{X509NameType} instances should compare based on their NIDs.
        """
        def _equality(a, b, assertTrue, assertFalse):
            assertTrue(a == b, "(%r == %r) --> False" % (a, b))
            assertFalse(a != b)
            assertTrue(b == a)
            assertFalse(b != a)

        def assertEqual(a, b):
            _equality(a, b, self.assertTrue, self.assertFalse)

        # Instances compare equal to themselves.
        name = self._x509name()
        assertEqual(name, name)

        # Empty instances should compare equal to each other.
        assertEqual(self._x509name(), self._x509name())

        # Instances with equal NIDs should compare equal to each other.
        assertEqual(self._x509name(commonName="foo"),
                    self._x509name(commonName="foo"))

        # Instance with equal NIDs set using different aliases should compare
        # equal to each other.
        assertEqual(self._x509name(commonName="foo"),
                    self._x509name(CN="foo"))

        # Instances with more than one NID with the same values should compare
        # equal to each other.
        assertEqual(self._x509name(CN="foo", organizationalUnitName="bar"),
                    self._x509name(commonName="foo", OU="bar"))

        def assertNotEqual(a, b):
            _equality(a, b, self.assertFalse, self.assertTrue)

        # Instances with different values for the same NID should not compare
        # equal to each other.
        assertNotEqual(self._x509name(CN="foo"),
                       self._x509name(CN="bar"))

        # Instances with different NIDs should not compare equal to each other.
        assertNotEqual(self._x509name(CN="foo"),
                       self._x509name(OU="foo"))

        def _inequality(a, b, assertTrue, assertFalse):
            assertTrue(a < b)
            assertTrue(a <= b)
            assertTrue(b > a)
            assertTrue(b >= a)
            assertFalse(a > b)
            assertFalse(a >= b)
            assertFalse(b < a)
            assertFalse(b <= a)

        def assertLessThan(a, b):
            _inequality(a, b, self.assertTrue, self.assertFalse)

        # An X509Name with a NID with a value which sorts less than the value
        # of the same NID on another X509Name compares less than the other
        # X509Name.
        assertLessThan(self._x509name(CN="abc"),
                       self._x509name(CN="def"))

        def assertGreaterThan(a, b):
            _inequality(a, b, self.assertFalse, self.assertTrue)

        # An X509Name with a NID with a value which sorts greater than the
        # value of the same NID on another X509Name compares greater than the
        # other X509Name.
        assertGreaterThan(self._x509name(CN="def"),
                          self._x509name(CN="abc"))


    def test_hash(self):
        """
        L{X509Name.hash} returns an integer hash based on the value of the
        name.
        """
        a = self._x509name(CN="foo")
        b = self._x509name(CN="foo")
        self.assertEqual(a.hash(), b.hash())
        a.CN = "bar"
        self.assertNotEqual(a.hash(), b.hash())


    def test_der(self):
        """
        L{X509Name.der} returns the DER encoded form of the name.
        """
        a = self._x509name(CN="foo", C="US")
        self.assertEqual(
            a.der(),
            '0\x1b1\x0b0\t\x06\x03U\x04\x06\x13\x02US'
            '1\x0c0\n\x06\x03U\x04\x03\x13\x03foo')



class _PKeyInteractionTestsMixin:
    """
    Tests which involve another thing and a PKey.
    """
    def signable(self):
        """
        Return something with a C{set_pubkey}, C{set_pubkey}, and C{sign} method.
        """
        raise NotImplementedError()


    def test_signWithUngenerated(self):
        """
        L{X509Req.sign} raises L{ValueError} when pass a L{PKey} with no parts.
        """
        request = self.signable()
        key = PKey()
        self.assertRaises(ValueError, request.sign, key, 'MD5')


    def test_signWithPublicKey(self):
        """
        L{X509Req.sign} raises L{ValueError} when pass a L{PKey} with no
        private part as the signing key.
        """
        request = self.signable()
        key = PKey()
        key.generate_key(TYPE_RSA, 512)
        request.set_pubkey(key)
        pub = request.get_pubkey()
        self.assertRaises(ValueError, request.sign, pub, 'MD5')



class X509ReqTests(TestCase, _PKeyInteractionTestsMixin, _Python23TestCaseHelper):
    """
    Tests for L{OpenSSL.crypto.X509Req}.
    """
    def signable(self):
        """
        Create and return a new L{X509Req}.
        """
        return X509Req()


    def test_construction(self):
        """
        L{X509Req} takes no arguments and returns an L{X509ReqType} instance.
        """
        request = X509Req()
        self.assertTrue(
            isinstance(request, X509ReqType),
            "%r is of type %r, should be %r" % (request, type(request), X509ReqType))


    def test_get_subject(self):
        """
        L{X509ReqType.get_subject} returns an L{X509Name} for the subject of
        the request and which is valid even after the request object is
        otherwise dead.
        """
        request = X509Req()
        subject = request.get_subject()
        self.assertTrue(
            isinstance(subject, X509NameType),
            "%r is of type %r, should be %r" % (subject, type(subject), X509NameType))
        subject.commonName = "foo"
        self.assertEqual(request.get_subject().commonName, "foo")
        del request
        subject.commonName = "bar"
        self.assertEqual(subject.commonName, "bar")



class X509Tests(TestCase, _PKeyInteractionTestsMixin, _Python23TestCaseHelper):
    """
    Tests for L{OpenSSL.crypto.X509}.
    """
    pemData = """
-----BEGIN CERTIFICATE-----
MIICfTCCAeYCAQEwDQYJKoZIhvcNAQEEBQAwgYYxCzAJBgNVBAYTAlVTMRkwFwYD
VQQDExBweW9wZW5zc2wuc2YubmV0MREwDwYDVQQHEwhOZXcgWW9yazESMBAGA1UE
ChMJUHlPcGVuU1NMMREwDwYDVQQIEwhOZXcgWW9yazEQMA4GCSqGSIb3DQEJARYB
IDEQMA4GA1UECxMHVGVzdGluZzAeFw0wODAzMjUxOTA0MTNaFw0wOTAzMjUxOTA0
MTNaMIGGMQswCQYDVQQGEwJVUzEZMBcGA1UEAxMQcHlvcGVuc3NsLnNmLm5ldDER
MA8GA1UEBxMITmV3IFlvcmsxEjAQBgNVBAoTCVB5T3BlblNTTDERMA8GA1UECBMI
TmV3IFlvcmsxEDAOBgkqhkiG9w0BCQEWASAxEDAOBgNVBAsTB1Rlc3RpbmcwgZ8w
DQYJKoZIhvcNAQEBBQADgY0AMIGJAoGBANp6Y17WzKSwBsUWkXdqg6tnXy8H8hA1
msCMWpc+/2KJ4mbv5NyD6UD+/SqagQqulPbF/DFea9nAE0zhmHJELcM8gUTIlXv/
cgDWnmK4xj8YkjVUiCdqKRAKeuzLG1pGmwwF5lGeJpXNxQn5ecR0UYSOWj6TTGXB
9VyUMQzCClcBAgMBAAEwDQYJKoZIhvcNAQEEBQADgYEAmm0Vzvv1O91WLl2LnF2P
q55LJdOnJbCCXIgxLdoVmvYAz1ZJq1eGKgKWI5QLgxiSzJLEU7KK//aVfiZzoCd5
RipBiEEMEV4eAY317bHPwPP+4Bj9t0l8AsDLseC5vLRHgxrLEu3bn08DYx6imB5Q
UBj849/xpszEM7BhwKE0GiQ=
-----END CERTIFICATE-----
-----BEGIN RSA PRIVATE KEY-----
MIICXAIBAAKBgQDaemNe1syksAbFFpF3aoOrZ18vB/IQNZrAjFqXPv9iieJm7+Tc
g+lA/v0qmoEKrpT2xfwxXmvZwBNM4ZhyRC3DPIFEyJV7/3IA1p5iuMY/GJI1VIgn
aikQCnrsyxtaRpsMBeZRniaVzcUJ+XnEdFGEjlo+k0xlwfVclDEMwgpXAQIDAQAB
AoGBALi0a7pMQqqgnriVAdpBVJveQtxSDVWi2/gZMKVZfzNheuSnv4amhtaKPKJ+
CMZtHkcazsE2IFvxRN/kgato9H3gJqq8nq2CkdpdLNVKBoxiCtkLfutdY4SQLtoY
USN7exk131pchsAJXYlR6mCW+ZP+E523cNwpPgsyKxVbmXSBAkEA9470fy2W0jFM
taZFslpntKSzbvn6JmdtjtvWrM1bBaeeqFiGBuQFYg46VaCUaeRWYw02jmYAsDYh
ZQavmXThaQJBAOHtlAQ0IJJEiMZr6vtVPH32fmbthSv1AUSYPzKqdlQrUnOXPQXu
z70cFoLG1TvPF5rBxbOkbQ/s8/ka5ZjPfdkCQCeC7YsO36+UpsWnUCBzRXITh4AC
7eYLQ/U1KUJTVF/GrQ/5cQrQgftwgecAxi9Qfmk4xqhbp2h4e0QAmS5I9WECQH02
0QwrX8nxFeTytr8pFGezj4a4KVCdb2B3CL+p3f70K7RIo9d/7b6frJI6ZL/LHQf2
UP4pKRDkgKsVDx7MELECQGm072/Z7vmb03h/uE95IYJOgY4nfmYs0QKA9Is18wUz
DpjfE33p0Ha6GO1VZRIQoqE24F8o5oimy3BEjryFuw4=
-----END RSA PRIVATE KEY-----
"""

    def signable(self):
        """
        Create and return a new L{X509}.
        """
        return X509()


    def test_construction(self):
        """
        L{X509} takes no arguments and returns an instance of L{X509Type}.
        """
        certificate = X509()
        self.assertTrue(
            isinstance(certificate, X509Type),
            "%r is of type %r, should be %r" % (certificate,
                                                type(certificate),
                                                X509Type))


    def test_serial_number(self):
        """
        The serial number of an L{X509Type} can be retrieved and modified with
        L{X509Type.get_serial_number} and L{X509Type.set_serial_number}.
        """
        certificate = X509()
        self.assertRaises(TypeError, certificate.set_serial_number)
        self.assertRaises(TypeError, certificate.set_serial_number, 1, 2)
        self.assertRaises(TypeError, certificate.set_serial_number, "1")
        self.assertRaises(TypeError, certificate.set_serial_number, 5.5)
        self.assertEqual(certificate.get_serial_number(), 0)
        certificate.set_serial_number(1)
        self.assertEqual(certificate.get_serial_number(), 1)
        certificate.set_serial_number(2 ** 32 + 1)
        self.assertEqual(certificate.get_serial_number(), 2 ** 32 + 1)
        certificate.set_serial_number(2 ** 64 + 1)
        self.assertEqual(certificate.get_serial_number(), 2 ** 64 + 1)
        certificate.set_serial_number(2 ** 128 + 1)
        self.assertEqual(certificate.get_serial_number(), 2 ** 128 + 1)


    def _setBoundTest(self, which):
        """
        L{X509Type.set_notBefore} takes a string in the format of an ASN1
        GENERALIZEDTIME and sets the beginning of the certificate's validity
        period to it.
        """
        certificate = X509()
        set = getattr(certificate, 'set_not' + which)
        get = getattr(certificate, 'get_not' + which)

        # Starts with no value.
        self.assertEqual(get(), None)

        # GMT (Or is it UTC?) -exarkun
        when = "20040203040506Z"
        set(when)
        self.assertEqual(get(), when)

        # A plus two hours and thirty minutes offset
        when = "20040203040506+0530"
        set(when)
        self.assertEqual(get(), when)

        # A minus one hour fifteen minutes offset
        when = "20040203040506-0115"
        set(when)
        self.assertEqual(get(), when)

        # An invalid string results in a ValueError
        self.assertRaises(ValueError, set, "foo bar")


    def test_set_notBefore(self):
        """
        L{X509Type.set_notBefore} takes a string in the format of an ASN1
        GENERALIZEDTIME and sets the beginning of the certificate's validity
        period to it.
        """
        self._setBoundTest("Before")


    def test_set_notAfter(self):
        """
        L{X509Type.set_notAfter} takes a string in the format of an ASN1
        GENERALIZEDTIME and sets the end of the certificate's validity period
        to it.
        """
        self._setBoundTest("After")


    def test_get_notBefore(self):
        """
        L{X509Type.get_notBefore} returns a string in the format of an ASN1
        GENERALIZEDTIME even for certificates which store it as UTCTIME
        internally.
        """
        cert = load_certificate(FILETYPE_PEM, self.pemData)
        self.assertEqual(cert.get_notBefore(), "20080325190413Z")


    def test_get_notAfter(self):
        """
        L{X509Type.get_notAfter} returns a string in the format of an ASN1
        GENERALIZEDTIME even for certificates which store it as UTCTIME
        internally.
        """
        cert = load_certificate(FILETYPE_PEM, self.pemData)
        self.assertEqual(cert.get_notAfter(), "20090325190413Z")


    def test_digest(self):
        """
        L{X509.digest} returns a string giving ":"-separated hex-encoded words
        of the digest of the certificate.
        """
        cert = X509()
        self.assertEqual(
            cert.digest("md5"),
            "A8:EB:07:F8:53:25:0A:F2:56:05:C5:A5:C4:C4:C7:15")
