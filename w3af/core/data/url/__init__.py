import ssl

try:
    # 2.7.9 enabled certificate verification by default for stdlib http clients
    # https://www.python.org/dev/peps/pep-0476/
    #
    # We don't want that, so we're disabling it globally
    # https://github.com/andresriancho/w3af/issues/8115
    #
    # pylint: disable=E1101
    ssl._create_default_https_context = ssl._create_unverified_context
    # pylint: enable=E1101
except AttributeError:
    pass