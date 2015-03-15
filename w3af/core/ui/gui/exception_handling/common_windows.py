"""
common_windows_report.py

Copyright 2012 Andres Riancho

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
import gtk
import Queue
import threading
import gobject

from w3af.core.ui.gui.helpers import end_threads, Throbber
from w3af.core.ui.gui.entries import EmailEntry
from w3af.core.ui.gui.constants import W3AF_ICON
from w3af.core.controllers.easy_contribution.github_issues import (GithubIssues,
                                                                   OAUTH_TOKEN,
                                                                   LoginFailed,
                                                                   OAUTH_AUTH_FAILED,
                                                                   OAuthTokenInvalid,
                                                                   DEFAULT_BUG_QUERY_TEXT)


class SimpleBaseWindow(gtk.Window):

    def __init__(self, type=gtk.WINDOW_TOPLEVEL):
        """
        One simple class to create other windows.
        """
        super(SimpleBaseWindow, self).__init__(type=type)

        self.connect("delete-event", self._handle_cancel)
        self.connect("destroy", self._handle_cancel)

        self.set_icon_from_file(W3AF_ICON)

    def _handle_cancel(self, *args):
        end_threads()
        self.destroy()


class bug_report_worker(threading.Thread):
    """
    The simplest threading object possible to report bugs to the network without
    blocking the UI.
    """
    FINISHED = -1

    def __init__(self, bug_report_function, bugs_to_report):
        threading.Thread.__init__(self)
        self.daemon = True
        
        self.bug_report_function = bug_report_function
        self.bugs_to_report = bugs_to_report
        self.output = Queue.Queue()

    def run(self):
        """
        The thread's main method, where all the magic happens.
        """
        for bug in self.bugs_to_report:
            result = apply(self.bug_report_function, bug)
            self.output.put(result)

        self.output.put(self.FINISHED)


class report_bug_show_result(gtk.MessageDialog):
    """
    A class that shows the result of one or more bug reports to the user. The
    window shows a "Thanks" message and links to the bugs that were generated.

    Unlike previous versions, this window actually sends the bugs to the network
    since we want to show the ticket IDs "in real time" to the user instead of
    reporting them all and then showing a long list of items.
    """

    def __init__(self, bug_report_function, bugs_to_report):
        """
        :param bug_report_function: The function that's used to report bugs.
                                    apply(bug_report_function, bug_to_report)

        :param bugs_to_report: An iterable with the bugs to report. These are
                               going to be the parameters for the
                               bug_report_function.
        """
        gtk.MessageDialog.__init__(self,
                                   None,
                                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_INFO,
                                   gtk.BUTTONS_OK,
                                   None)

        self.bug_report_function = bug_report_function
        self.bugs_to_report = bugs_to_report
        self.ticket_ids_in_markup = 0
        self.reported_ids = []

        self.set_title('Bug report results')
        self.set_icon_from_file(W3AF_ICON)

        # Disable OK button until the worker finishes the bug reporting process
        self.ok_button = self.get_widget_for_response(gtk.RESPONSE_OK)
        self.ok_button.set_sensitive(False)

    def run(self):
        #
        #    Main text
        #
        text = ('Thank you for reporting your bugs, it helps us improve our'
                ' scanning engine. If you want to get involved with the project'
                ' please send an email to our <a href="mailto:%s">mailing list'
                ' </a>.')
        text %= 'w3af-develop@lists.sourceforge.net'
        # All these lines are here to add a label instead of the easy "set_
        # markup" in order to avoid a bug where the label text appears selected
        msg_area = self.get_message_area()
        [msg_area.remove(c) for c in msg_area.get_children()]
        label = gtk.Label()
        label.set_markup(text)
        label.set_line_wrap(True)
        label.select_region(0, 0)
        msg_area.pack_start(label)

        self.worker = bug_report_worker(
            self.bug_report_function, self.bugs_to_report)
        self.worker.start()
        gobject.timeout_add(200, self.add_result_from_worker)

        self.status_hbox = gtk.HBox()

        #
        #    Empty markup for the ticket ids
        #
        self.link_label = gtk.Label('')
        self.link_label.set_line_wrap(True)
        self.link_label.set_use_markup(True)
        self.status_hbox.pack_end(self.link_label)

        #
        #    Throbber, only show while still running.
        #

        self.throbber = Throbber()
        self.throbber.running(True)
        self.status_hbox.pack_end(self.throbber)

        #
        #    Check, hidden at the beginning
        #    http://www.pygtk.org/docs/pygtk/gtk-stock-items.html
        #
        self.done_icon = gtk.Image()
        self.done_icon.set_from_stock(gtk.STOCK_YES, gtk.ICON_SIZE_BUTTON)
        self.status_hbox.pack_end(self.done_icon)

        self.vbox.pack_start(self.status_hbox, True, True)

        self.add(self.vbox)
        self.show_all()
        self.done_icon.hide()

        super(report_bug_show_result, self).run()
        self.destroy()

        return self.reported_ids

    def add_result_from_worker(self):
        """
        Adds the results from the worker to the text that's shown in the window
        """
        # The links to the reported tickets
        try:
            bug_report_result = self.worker.output.get(block=False)
        except Queue.Empty:
            # The worker is reporting stuff to the network and doesn't
            # have any results at this moment. Call me in some seconds.
            return True

        if bug_report_result == self.worker.FINISHED:
            self.throbber.running(False)
            self.throbber.hide()
            self.done_icon.show()
            self.ok_button.set_sensitive(True)
            # don't call me anymore !
            return False
        else:
            # Add the data to the label and ask to be called again
            ticket_id, ticket_url = bug_report_result
            self.add_link(ticket_id, ticket_url)
            return True

    def add_link(self, ticket_id, ticket_url):
        self.reported_ids.append(ticket_id)

        new_link = '<a href="%s">%s</a>'
        new_link = new_link % (ticket_url, ticket_id)

        current_markup = self.link_label.get_label()

        needs_new_line = False
        if self.ticket_ids_in_markup == 4:
            needs_new_line = True
            self.ticket_ids_in_markup = 0
        else:
            self.ticket_ids_in_markup += 1

        needs_delim = True
        if len(current_markup) == 0 or needs_new_line:
            needs_delim = False

        current_markup += (
            '\n' if needs_new_line else '') + (', ' if needs_delim else '')
        current_markup += new_link

        self.link_label.set_markup(current_markup)


class dlg_ask_credentials(gtk.MessageDialog):
    """
    A dialog that allows any exception handler to ask the user for his
    credentials before sending any bug report information to the network. The
    supported types of credentials are:

        * Anonymous
        * Email
        * Sourceforge user (soon to be deprecated, nobody uses it).

    """

    METHOD_ANON = 1
    METHOD_EMAIL = 2
    METHOD_GH = 3

    def __init__(self, invalid_login=False):
        """
        :return: A tuple with the following information:
                    (user_exit, method, params)

                Where method is one of METHOD_ANON, METHOD_EMAIL, METHOD_GH and,
                params is the email or the sourceforge username and password,
                in the anon case, the params are empty.
        """
        gtk.MessageDialog.__init__(self,
                                   None,
                                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_QUESTION,
                                   gtk.BUTTONS_OK,
                                   None)

        self._invalid_login = invalid_login

        self.set_icon_from_file(W3AF_ICON)
        self.set_title('Bug report method - Step 1/2')

    def run(self):
        """
        Setup the dialog and return the results to the invoker.
        """
        msg = _('\nChoose how to report the bug(s)')

        if self._invalid_login:
            msg += _(
                '<b><i>Invalid credentials, please try again.</i></b>\n\n')

        self.set_markup(msg)

        #
        #    Anon
        #
        anon_button = gtk.RadioButton(None, "Anonymously")
        anon_button.set_active(True)
        self.vbox.pack_start(anon_button, True, True, 0)

        separator = gtk.HSeparator()
        self.vbox.pack_start(separator, True, True, 0)

        #
        #    Email
        #
        email_button = gtk.RadioButton(anon_button, "Use email address")
        self.vbox.pack_start(email_button, True, True, 0)

        # Create the text input field
        self.email_entry = EmailEntry(self._email_entry_changed)
        self.email_entry.connect(
            "activate", lambda x: self.response(gtk.RESPONSE_OK))

        # Create a horizontal box to pack the entry and a label
        email_hbox = gtk.HBox()
        email_hbox.pack_start(gtk.Label("Email address:"), False, 5, 5)
        email_hbox.pack_end(self.email_entry)
        email_hbox.set_sensitive(False)
        self.vbox.pack_start(email_hbox, True, True, 0)

        separator = gtk.HSeparator()
        self.vbox.pack_start(separator, True, True, 0)

        #
        #    Github credentials
        #
        gh_button = gtk.RadioButton(email_button, "GitHub credentials:")
        self.vbox.pack_start(gh_button, True, True, 0)

        gh_vbox = gtk.VBox()

        # Create the text input field
        user_entry = gtk.Entry()
        user_entry.connect(
            "activate", lambda x: self.response(gtk.RESPONSE_OK))

        user_hbox = gtk.HBox()
        user_hbox.pack_start(gtk.Label("Username:  "), False, 5, 5)
        user_hbox.pack_end(user_entry)
        gh_vbox.pack_start(user_hbox, True, True, 0)

        # Create the password entry
        passwd_entry = gtk.Entry()
        passwd_entry.set_visibility(False)
        passwd_entry.connect(
            "activate", lambda x: self.response(gtk.RESPONSE_OK))

        passwd_hbox = gtk.HBox()
        passwd_hbox.pack_start(gtk.Label("Password:  "), False, 5, 5)
        passwd_hbox.pack_end(passwd_entry)
        gh_vbox.pack_start(passwd_hbox, True, True, 0)

        # Some secondary text
        warning_label = gtk.Label()
        warning = _("\nYour credentials won't be stored in your computer,\n"
                    "  and will only be sent over HTTPS connections.")
        warning_label.set_text(warning)
        gh_vbox.pack_start(warning_label, True, True, 0)
        gh_vbox.set_sensitive(False)
        self.vbox.pack_start(gh_vbox, True, True, 0)

        separator = gtk.HSeparator()
        self.vbox.pack_start(separator, True, True, 0)

        # Handling of sensitiviness between the radio contents
        anon_button.connect("toggled", self._radio_callback_anon, [
        ], [email_hbox, gh_vbox])
        email_button.connect("toggled", self._radio_callback_email,
                             [email_hbox, ], [gh_vbox, ])
        gh_button.connect(
            "toggled", self._radio_callback_gh, [gh_vbox, ], [email_hbox, ])

        # Go go go!
        self.show_all()
        gtk_response = super(dlg_ask_credentials, self).run()

        # The user closed the dialog with the X
        if gtk_response == gtk.RESPONSE_DELETE_EVENT:
            return True, None, None

        #
        # Get the results, generate the result tuple and return
        #
        active_label = [r.get_label(
        ) for r in anon_button.get_group() if r.get_active()]
        active_label = active_label[0].lower()

        if 'email' in active_label:
            method = self.METHOD_EMAIL
            email = self.email_entry.get_text()
            params = (email,)
        elif 'sourceforge' in active_label:
            method = self.METHOD_GH
            user = user_entry.get_text()
            passwd = passwd_entry.get_text()
            params = (user, passwd)
        else:
            method = self.METHOD_ANON
            params = ()

        # I'm done!
        self.destroy()

        return False, method, params

    def _email_entry_changed(self, x, y):
        """
        Disable the OK button if the email is invalid
        """
        ok_button = self.get_widget_for_response(gtk.RESPONSE_OK)

        if self.email_entry.is_valid():
            # Activate OK button
            ok_button.set_sensitive(True)
        else:
            # Disable OK button
            ok_button.set_sensitive(False)

    def _radio_callback_anon(self, event, enable, disable):
        self._radio_callback(event, enable, disable)
        # re-enable the button in case it was disabled by an invalid email
        # address entry
        ok_button = self.get_widget_for_response(gtk.RESPONSE_OK)
        ok_button.set_sensitive(True)

    def _radio_callback_email(self, event, enable, disable):
        self._radio_callback(event, enable, disable)
        self._email_entry_changed(True, True)

    def _radio_callback_gh(self, event, enable, disable):
        self._radio_callback(event, enable, disable)
        # re-enable the button in case it was disabled by an invalid email
        # address entry
        ok_button = self.get_widget_for_response(gtk.RESPONSE_OK)
        ok_button.set_sensitive(True)

    def _radio_callback(self, event, enable, disable):
        """
        Handle the clicks on the different radio buttons.
        """
        for section in enable:
            section.set_sensitive(True)

        for section in disable:
            section.set_sensitive(False)


def dlg_invalid_token(parent):
    md = gtk.MessageDialog(parent,
                           gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                           gtk.MESSAGE_WARNING,
                           gtk.BUTTONS_OK,
                           OAUTH_AUTH_FAILED)

    md.set_icon_from_file(W3AF_ICON)
    md.set_title('GitHub authentication failed')
    return md


class dlg_ask_bug_info(gtk.MessageDialog):

    def __init__(self, invalid_login=False):
        """
        :return: A tuple with the following information:
                    (user_exit, bug_summary, bug_description)

        """
        gtk.MessageDialog.__init__(self,
                                   None,
                                   gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_QUESTION,
                                   gtk.BUTTONS_OK,
                                   None)

        self.set_icon_from_file(W3AF_ICON)
        self.set_title('Bug information - Step 2/2')

    def run(self):
        msg = 'Please provide the following information about the bug\n'
        self.set_markup(msg)

        #create the text input field
        summary_entry = gtk.Entry()

        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        description_text_view = gtk.TextView()
        description_text_view.set_size_request(240, 300)
        description_text_view.set_wrap_mode(gtk.WRAP_WORD)
        buffer = description_text_view.get_buffer()
        buffer.set_text(DEFAULT_BUG_QUERY_TEXT)
        sw.add(description_text_view)

        #create a horizontal box to pack the entry and a label
        summary_hbox = gtk.HBox()
        summary_hbox.pack_start(gtk.Label("Summary    "), False, 5, 5)
        summary_hbox.pack_end(summary_entry)

        description_hbox = gtk.HBox()
        description_hbox.pack_start(gtk.Label("Description"), False, 5, 5)
        description_hbox.pack_start(sw, True, True, 0)

        #add it and show it
        self.vbox.pack_start(summary_hbox, True, True, 0)
        self.vbox.pack_start(description_hbox, True, True, 0)
        self.show_all()

        # Go go go
        gtk_response = super(dlg_ask_bug_info, self).run()

        # The user closed the dialog with the X
        if gtk_response == gtk.RESPONSE_DELETE_EVENT:
            return True, None, None

        summary = summary_entry.get_text()
        description = buffer.get_text(
            buffer.get_start_iter(), buffer.get_end_iter())

        self.destroy()

        return False, summary, description


class GithubBugReport(object):
    """
    Class that models user interaction with Github to report ONE bug.
    """

    def __init__(self, tback='', fname=None, plugins=''):
        self.gh = None
        self.tback = tback
        self.fname = fname
        self.plugins = plugins
        self.autogen = False

    def report_bug(self):
        user_exit, gh, summary, userdesc, email = self._info_and_login()

        if user_exit:
            return

        rbsr = report_bug_show_result(self._report_bug_to_github,
                                      [(gh, summary, userdesc, email), ])
        rbsr.run()

    def _info_and_login(self):
        # Do the login
        user_exit, gh, email = self._login_github()

        if user_exit:
            return user_exit, None, None, None, None

        # Ask for a bug title and description
        dlg_bug_info = dlg_ask_bug_info()
        user_exit, summary, userdesc = dlg_bug_info.run()

        if user_exit:
            return user_exit, None, None, None, None

        return user_exit, gh, summary, userdesc, email

    def _report_bug_to_github(self, gh, summary, userdesc, email):
        """
        Send bug to github.
        """
        try:
            ticket_url, ticket_id = gh.report_bug(summary, userdesc, self.tback,
                                                  self.fname, self.plugins,
                                                  self.autogen, email)
        except:
            return None, None
        else:
            return ticket_url, ticket_id

    def _login_github(self, retry=3):
        """
        Perform user login.

        :return: (user wants to exit,
                  github instance,
                  user's email)
        """
        invalid_login = False
        email = None

        while retry:
            # Decrement retry counter
            retry -= 1

            # Ask for user and password, or anonymous
            dlg_cred = dlg_ask_credentials(invalid_login)
            user_exit, method, params = dlg_cred.run()
            dlg_cred.destroy()

            # The user closed the dialog and wants to exit
            if user_exit:
                return user_exit, None, None

            if method == dlg_ask_credentials.METHOD_GH:
                user, password = params

            elif method == dlg_ask_credentials.METHOD_EMAIL:
                # The user chose METHOD_ANON or METHOD_EMAIL with both these
                # methods the framework actually logs in using our default
                # credentials
                user, password = (OAUTH_TOKEN, None)
                email = params[0]

            else:
                # The user chose METHOD_ANON or METHOD_EMAIL with both these
                # methods the framework actually logs in using our default
                # credentials
                user, password = (OAUTH_TOKEN, None)

            try:
                gh = GithubIssues(user, password)
                gh.login()
            except LoginFailed:
                # Let the user try again
                invalid_login = True
                continue
            except OAuthTokenInvalid:
                dlg = dlg_invalid_token(self)
                dlg.run()
                dlg.destroy()
                return True, None, None
            else:
                # Login success!
                break

        return False, gh, email


class GithubMultiBugReport(GithubBugReport):
    """
    Class that models user interaction with Github to report ONE OR MORE bugs.
    """

    def __init__(self, exception_list, scan_id):
        GithubBugReport.__init__(self)
        self.gh = None
        self.exception_list = exception_list
        self.scan_id = scan_id
        self.autogen = False

    def report_bug(self):
        user_exit, gh, email = self._login_github()

        if user_exit:
            return

        bug_info_list = []
        for edata in self.exception_list:
            tback = edata.get_details()
            plugins = edata.enabled_plugins
            bug_info_list.append((gh, tback, self.scan_id, email, plugins))

        rbsr = report_bug_show_result(self._report_bug_to_github, bug_info_list)
        rbsr.run()

    def _report_bug_to_github(self, gh, tback, scan_id, email, plugins):
        """
        Send bug to github.
        """
        userdesc = 'No user description was provided for this bug report given'\
                   ' that it was related to handled exceptions in scan with id'\
                   ' %s' % scan_id
        try:
            ticket_url, ticket_id = gh.report_bug(None, userdesc, tback=tback,
                                                  plugins=plugins,
                                                  autogen=self.autogen,
                                                  email=email)
        except:
            return None, None
        else:
            return ticket_url, ticket_id
