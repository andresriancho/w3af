import hashlib


def gen_hash(request):
    """
    Generate an unique ID for a request

    Note that we use safe_str function in order to avoid errors like:
        * Encoding error #1917
        * https://github.com/andresriancho/w3af/issues/1917
    """
    req = request
    headers_1 = ''.join('%s%s' % (safe_str(h), safe_str(v)) for h, v in req.headers.iteritems())
    headers_2 = ''.join('%s%s' % (safe_str(h), safe_str(v)) for h, v in req.unredirected_hdrs.iteritems())
    
    the_str = '%s%s%s%s%s' % (safe_str(req.get_method()),
                              safe_str(req.get_full_url()),
                              headers_1,
                              headers_2,
                              safe_str(req.get_data() or ''))

    return hashlib.md5(the_str).hexdigest()


def safe_str(obj):
    """
    http://code.activestate.com/recipes/466341-guaranteed-conversion-to-unicode-or-byte-string/

    :return: The byte string representation of obj
    """
    try:
        return str(obj)
    except UnicodeEncodeError:
        # obj is unicode
        return unicode(obj).encode('unicode_escape')
