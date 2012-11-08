"""
    pygtkhelpers.test
    ~~~~~~~~~~~~~~~~~

    Assistance for unittesting pygtk

    :copyright: 2005-2008 by pygtkhelpers Authors
    :license: LGPL 2 or later (see README/COPYING/LICENSE)
"""

class CheckCalled(object):
    """Utility to check whether a signal has been emitted

    :param object: The Object that will fire the signal
    :param signal: The signal name

    This class should be used when testing whether a signal has been called.
    It could be used in conjuntion with :func:`pygtkhelpers.utils.refresh_gui`
    in order to block the UI adequately to check::

        >>> import gtk
        >>> from pygtkhelpers.utils import refresh_gui
        >>> b = gtk.Button('ABC')
        >>> check = CheckCalled(b, 'clicked')
        >>> b.clicked()
        >>> assert check.called
        >>> assert check.called_count == 1
        >>> b.clicked()
        >>> assert check.called_count == 2

    """
    def __init__(self, _object, signal):
        self.called = None
        self.called_count = 0
        _object.connect(signal, self)

    def __call__(self, *k):
        self.called = k
        self.called_count += 1

    def __str__(self):
        return '<check_called object with %s calls>' % self.called_count