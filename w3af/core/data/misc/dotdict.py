from w3af.core.data.misc.encoding import smart_str_ignore, smart_unicode


class dotdict(dict):
    """dot.notation access to dictionary attributes"""

    def __setattr__(self, key, value):
        """
        Overriding in order to translate every value to an unicode object

        :param key: The attribute name to set
        :param value: The value (string, unicode or anything else)
        :return: None
        """
        if isinstance(value, basestring):
            value = smart_unicode(value)

        self[key] = value

    #__setattr__ = dict.__setitem__
    __getattr__ = dict.get
    __delattr__ = dict.__delitem__