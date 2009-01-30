# Copyright (C) Jean-Paul Calderone 2008, All rights reserved

"""
Unit tests for L{OpenSSL.SSL}.
"""

from unittest import TestCase

from OpenSSL.crypto import TYPE_RSA, PKey
from OpenSSL.SSL import Context
from OpenSSL.SSL import SSLv2_METHOD, SSLv3_METHOD, SSLv23_METHOD, TLSv1_METHOD


class ContextTests(TestCase):
    """
    Unit tests for L{OpenSSL.SSL.Context}.
    """
    def test_method(self):
        """
        L{Context} can be instantiated with one of L{SSLv2_METHOD},
        L{SSLv3_METHOD}, L{SSLv23_METHOD}, or L{TLSv1_METHOD}.
        """
        for meth in [SSLv2_METHOD, SSLv3_METHOD, SSLv23_METHOD, TLSv1_METHOD]:
            Context(meth)
        self.assertRaises(TypeError, Context, "")
        self.assertRaises(ValueError, Context, 10)


    def test_use_privatekey(self):
        """
        L{Context.use_privatekey} takes an L{OpenSSL.crypto.PKey} instance.
        """
        key = PKey()
        key.generate_key(TYPE_RSA, 128)
        ctx = Context(TLSv1_METHOD)
        ctx.use_privatekey(key)
        self.assertRaises(TypeError, ctx.use_privatekey, "")
