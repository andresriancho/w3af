# -*- coding: utf-8 -*-
"""
html_file.py

Copyright 2006 Andres Riancho

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
import os
import time
import datetime
import functools
import markdown

from jinja2 import StrictUndefined, Environment, FileSystemLoader

import w3af.core.data.kb.knowledge_base as kb
import w3af.core.data.kb.config as cf

from w3af import ROOT_PATH
from w3af.core.controllers.exceptions import DBException
from w3af.core.controllers.plugins.output_plugin import OutputPlugin
from w3af.core.data.misc.encoding import smart_unicode
from w3af.core.data.db.history import HistoryItem
from w3af.core.data.db.disk_list import DiskList
from w3af.core.data.options.opt_factory import opt_factory
from w3af.core.data.options.option_types import OUTPUT_FILE, INPUT_FILE
from w3af.core.data.options.option_list import OptionList


class html_file(OutputPlugin):
    """
    Generate HTML report with identified vulnerabilities and log messages.

    :author: Andres Riancho ((andres.riancho@gmail.com))
    """
    def __init__(self):
        OutputPlugin.__init__(self)

        # Internal variables
        self._initialized = False
        self._additional_info = DiskList(table_prefix='html_file')
        self._enabled_plugins = {}
        self.template_root = os.path.join(ROOT_PATH, 'plugins', 'output',
                                          'html_file', 'templates')

        # User configured parameters
        self._verbose = False
        self._output_file_name = '~/report.html'
        self._template = os.path.join(self.template_root, 'complete.html')

    def debug(self, message, new_line=True):
        """
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take
        an action for debug messages.
        """
        if self._verbose:
            to_print = self._clean_string(message)
            self._append_additional_info(to_print, 'debug')

    def do_nothing(self, *args, **kwargs):
        pass

    information = vulnerability = do_nothing

    def error(self, message, new_line=True):
        """
        This method is called from the output object. The output object was
        called from a plugin or from the framework. This method should take
        an action for error messages.
        """
        to_print = self._clean_string(message)
        self._append_additional_info(to_print, 'error')

    def console(self, message, new_line=True):
        """
        This method is used by the w3af console to print messages to the
        outside.
        """
        to_print = self._clean_string(message)
        self._append_additional_info(to_print, 'console')

    def _append_additional_info(self, message, msg_type):
        """
        Add a message to the debug table.

        :param message: The message to add to the table. It's in HTML.
        :param msg_type: The type of message
        """
        now = time.localtime(time.time())
        the_time = time.strftime("%c", now)
        self._additional_info.append((the_time, msg_type, message))

    def set_options(self, option_list):
        """
        Sets the Options given on the OptionList to self. The options are the
        result of a user entering some data on a window that was constructed
        using the XML Options that was retrieved from the plugin using
        get_options()

        This method MUST be implemented on every plugin.

        :return: No value is returned.
        """
        self._output_file_name = option_list['output_file'].get_value()
        self._verbose = option_list['verbose'].get_value()
        self._template = option_list['template'].get_value()

    def get_options(self):
        """
        :return: A list of option objects for this plugin.
        """
        ol = OptionList()

        d = 'The path to the HTML template used to render the report.'
        o = opt_factory('template', self._template, d, INPUT_FILE)
        ol.add(o)

        d = 'File name where this plugin will write to'
        o = opt_factory('output_file', self._output_file_name, d, OUTPUT_FILE)
        ol.add(o)

        d = 'True if debug information will be appended to the report.'
        o = opt_factory('verbose', self._verbose, d, 'boolean')
        ol.add(o)

        return ol

    def log_enabled_plugins(self, plugins_dict, options_dict):
        """
        This method is called from the output manager object. This method
        should take an action for the enabled plugins and their configuration.
        Usually, write the info to a file or print it somewhere.

        :param plugins_dict: A dict with all the plugin types and the
                                enabled plugins for that type of plugin.
        :param options_dict: A dict with the options for every plugin.
        """
        self._enabled_plugins = {}

        # TODO: Improve so it contains the plugin configuration too
        for plugin_type, enabled in plugins_dict.iteritems():
            self._enabled_plugins[plugin_type] = enabled

    def end(self):
        try:
            self.flush()
        finally:
            self._additional_info.clear()
            self._enabled_plugins = {}

    def flush(self):
        """
        This method is called when we want to write the data to the html,
        performs these main tasks:
            * Get the target URLs
            * Get the enabled plugins
            * Get the vulnerabilities and infos from the KB
            * Get the debug data
            * Send all the data to jinja2 for rendering the template
        """
        target_urls = [t.url_string for t in cf.cf.get('targets')]

        target_domain = 'unknown'

        target_domains = cf.cf.get('target_domains')
        if target_domains and len(target_domains) > 0:
            target_domain = target_domains[0]

        enabled_plugins = self._enabled_plugins
        findings = kb.kb.get_all_findings_iter()
        debug_log = ((t, l, smart_unicode(m)) for (t, l, m) in self._additional_info)
        known_urls = kb.kb.get_all_known_urls()

        context = {'target_urls': target_urls,
                   'target_domain': target_domain,
                   'enabled_plugins': enabled_plugins,
                   'findings': findings,
                   'debug_log': debug_log,
                   'known_urls': known_urls}

        # The file was verified to exist when setting the plugin configuration
        template_fh = file(os.path.expanduser(self._template), 'r')
        output_fh = file(os.path.expanduser(self._output_file_name), 'w')

        self._render_html_file(template_fh, context, output_fh)

    def _render_html_file(self, template_fh, context, output_fh):
        """
        Renders the HTML file using the configured template. Separated as a
        method to be able to easily test.

        :param context: A dict containing target urls, enabled plugins, etc.
        :return: True on successful rendering
        """
        severity_icon = functools.partial(get_severity_icon, self.template_root)

        env_config = {'undefined': StrictUndefined,
                      'trim_blocks': True,
                      'autoescape': True,
                      'lstrip_blocks': True}

        try:
            jinja2_env = Environment(**env_config)
        except TypeError:
            # Kali uses a different jinja2 version, which doesn't have the same
            # Environment kwargs, so we first try with the version we expect
            # to have available, and then if it doesn't work apply this
            # workaround for Kali
            #
            # https://github.com/andresriancho/w3af/issues/9552
            env_config.pop('lstrip_blocks')
            jinja2_env = Environment(**env_config)

        jinja2_env.filters['render_markdown'] = render_markdown
        jinja2_env.filters['request'] = request_dump
        jinja2_env.filters['response'] = response_dump
        jinja2_env.filters['severity_icon'] = severity_icon
        jinja2_env.filters['severity_text'] = get_severity_text
        jinja2_env.globals['get_current_date'] = get_current_date
        jinja2_env.loader = FileSystemLoader(self.template_root)

        template = jinja2_env.from_string(template_fh.read())

        report_stream = template.stream(context)
        report_stream.enable_buffering(5)

        for report_section in report_stream:
            output_fh.write(report_section.encode('utf-8'))

        return True

    def get_long_desc(self):
        """
        :return: A DETAILED description of the plugin functions and features.
        """
        return """
        This plugin writes the framework findings and messages to an HTML report

        Three configurable parameters exist:
            - template
            - output_file
            - verbose

        It is possible to customize the output by changing the template which
        is used to render the output file.

        If you want to write every HTTP request/response to a text file, you
        should use the text_file plugin.
        """


def render_markdown(markdown_text):
    """
    Render the vulndb/data contents (which are in markdown) to HTML

    :param markdown_text: The markdown from vulndb/data
    :return: HTML
    """
    return markdown.markdown(markdown_text)


def request_dump(_id):
    """
    :param _id: The ID to query in the database
    :return: The request as unicode
    """
    _history = HistoryItem()

    try:
        details = _history.read(_id)
    except DBException:
        return None

    return smart_unicode(details.request.dump().strip())


def response_dump(_id):
    """
    :param _id: The ID to query in the database
    :return: The response as unicode
    """
    _history = HistoryItem()

    try:
        details = _history.read(_id)
    except DBException:
        return None

    return smart_unicode(details.response.dump().strip())


def get_current_date():
    return datetime.date.today().strftime("%d.%m.%Y")


def get_severity_icon(template_root, severity):
    icon_file = os.path.join(template_root, '%s.png' % severity.lower())
    fmt = u'data:image/png;base64,%s'

    if os.path.exists(icon_file):
        return fmt % file(icon_file).read().encode('base64')

    return fmt


def get_severity_text(severity):
    if severity.lower() == 'information':
        severity = 'info'

    color_map = {'high': 'danger',
                 'medium': 'warning',
                 'low': 'success',
                 'info': 'info'}
    fmt = u'<h3 class="text-%s">%s</h3>'
    return fmt % (color_map[severity.lower()], severity.upper())