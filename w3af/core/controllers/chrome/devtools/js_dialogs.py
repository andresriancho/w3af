"""
js_dialogs.py

Copyright 2019 Andres Riancho

This file is part of w3af, http://w3af.org/ .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""


# This is the default dialog handler, it is used to dismiss alert, prompt, etc.
# which might appear during crawling.
def dialog_handler(_type, message):
    """
    Handles Page.javascriptDialogOpening event [0] which freezes the browser
    until it is dismissed.

    [0] https://chromedevtools.github.io/devtools-protocol/tot/Page#event-javascriptDialogOpening

    :param _type: One of alert, prompt, etc.
    :param message: The message shown in the aler / prompt
    :return: A tuple containing:
                * True if we want to dismiss the alert / prompt or False if we
                  want to cancel it.

                * The message to enter in the prompt (if this is a prompt).
    """
    return True, 'Bye!'

