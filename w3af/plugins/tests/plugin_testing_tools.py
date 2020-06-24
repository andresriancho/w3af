import inspect

from mock import patch

from w3af.core.controllers.plugins.auth_plugin import AuthPlugin
from w3af.core.data.url.HTTPResponse import HTTPResponse


class TestPluginError(Exception):
    pass


class TestPluginRunner:
    """
    This class prepares everything needed to run w3af plugin, offers special
    mocking (like mock_domain). The main method is `run_plugin`.
    """
    def __init__(self):
        self.plugin_last_ran = None  # last plugin instance used at self.run_plugin().
        # Useful for debugging.
        self.mocked_server = None

    def run_plugin(self, plugin, plugin_config=None, mock_domain=None, do_end_call=True):
        """
        :param Plugin plugin: plugin class or instance
        :param dict plugin_config:
        :param pytest.fixture mock_domain: pytest fixture to mock requests to
        specific domain
        :param bool do_end_call: if False plugin.end() won't be called
        """
        self._patch_network(mock_domain)

        if inspect.isclass(plugin):
            plugin_instance = plugin()
        else:
            plugin_instance = plugin

        self.plugin_last_ran = plugin_instance

        if plugin_config:
            self.set_options_to_plugin(plugin_instance, plugin_config)

        result = None
        did_plugin_run = False
        if isinstance(plugin_instance, AuthPlugin):
            result = self.run_auth_plugin(plugin_instance)
            did_plugin_run = True

        if do_end_call:
            plugin_instance.end()

        if not did_plugin_run:
            raise TestPluginError(
                "Can't find any way to run plugin {}. Is it already implemented?".format(
                    plugin_instance,
                )
            )
        return result

    @staticmethod
    def run_auth_plugin(plugin):
        if not plugin.has_active_session():
            return plugin.login()
        return False

    @staticmethod
    def set_options_to_plugin(plugin, options):
        """
        :param Plugin plugin: the plugin instance
        :param dict options: dict of options that will be set to plugin
        """
        options_list = plugin.get_options()
        for option_name, option_value in options.items():
            option = options_list[option_name]
            option.set_value(option_value)
        plugin.set_options(options_list)

    def _patch_network(self, mock_domain):
        self.mocked_server = MockedServer(url_mapping=mock_domain)
        patcher = patch(
            'w3af.core.data.url.extended_urllib.ExtendedUrllib.GET',
            self.mocked_server.mocked_GET,
        )
        patcher.start()
        chrome_patcher = patch(
            'w3af.core.controllers.chrome.instrumented.main.InstrumentedChrome.load_url',
            self.mocked_server.mocked_chrome_load_url(),
        )
        chrome_patcher.start()


class MockedServer:
    def __init__(self, url_mapping=None):
        self.url_mapping = url_mapping or {}
        self.default_content = '<html><body class="default">example.com</body></html>'
        self.response_count = 0
        self.urls_requested = []

    def mocked_GET(self, url, *args, **kwargs):
        if url in self.url_mapping:
            return self._mocked_resp(url, self.match_response(url))
        return self.default_content

    def mocked_chrome_load_url(self, *args, **kwargs):
        def real_mock(self_, url, *args, **kwargs):
            self_.chrome_conn.Page.reload()  # this enabled dom_analyzer.js
            response_content = self.match_response(url)
            result = self_.chrome_conn.Runtime.evaluate(
                expression='document.write(`{}`)'.format(response_content)
            )
            if result['result'].get('exceptionDetails'):
                error_text = (
                    "Can't mock the response for url\n"
                    "URL: {}\n"
                    "response_content: {}\n"
                    "JavaScript exception: {}"
                )
                raise TestPluginError(error_text.format(
                    url,
                    response_content,
                    result['result']['exceptionDetails']
                ))
            return None
        return real_mock

    def match_response(self, url):
        current_response_count = self.response_count
        self.response_count += 1
        self.urls_requested.append(url)
        if self.url_mapping.get(current_response_count):
            return self.url_mapping[current_response_count]
        if self.url_mapping.get(url.path):
            return self.url_mapping[url.path]
        return self.default_content

    @staticmethod
    def _mocked_resp(url, text_resp, *args, **kwargs):
        return HTTPResponse(
            code=200,
            read=text_resp,
            headers={},
            geturl=url,
            original_url=url,
        )

