from tblib.decorators import return_error


@return_error
def apply_with_return_error(args):
    """
    :see: https://github.com/ionelmc/python-tblib/issues/4
    """
    return args[0](*args[1:])
