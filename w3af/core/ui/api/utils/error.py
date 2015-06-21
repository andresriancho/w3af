from flask import jsonify


def abort(code, message):
    """
    Raise an exception to stop HTTP processing execution

    :param code: 403, 500, etc.
    :param message: A message to show to the user
    :return: None, an exception is raised
    """
    data = {'error': message,
            'code': code}
    raise NotImplementedError
