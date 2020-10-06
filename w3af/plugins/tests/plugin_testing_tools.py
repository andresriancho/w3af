import inspect
from urlparse import urlsplit

from mock import patch, MagicMock

from w3af.core.controllers.core_helpers.consumers.constants import POISON_PILL
from w3af.core.controllers.plugins.auth_plugin import AuthPlugin
from w3af.core.controllers.plugins.crawl_plugin import CrawlPlugin
from w3af.core.data.dc.headers import Headers
import w3af.core.data.kb.knowledge_base as kb
from w3af.core.data.parsers.doc.url import URL
from w3af.core.data.request.fuzzable_request import FuzzableRequest
from w3af.core.data.url.HTTPResponse import HTTPResponse
from w3af.core.data.url.extended_urllib import ExtendedUrllib


class TestPluginError(Exception):
    pass


class TestPluginRunner:
    """
    This class prepares everything needed to run w3af plugin, offers network
    mocking (like mock_domain). The main method is `run_plugin` and it should
    be used in tests. Also it exposes `plugin_last_ran` and `mocked_server`
    as parameters.
    """
    def __init__(self):
        # Useful for debugging:
        self.plugin_last_ran = None  # last plugin instance used at self.run_plugin().
        self.mocked_server = None  # mocked_server holds e.g. info which urls were hit.

    def run_plugin(
        self,
        plugin,
        plugin_config=None,
        mock_domain=None,
        do_end_call=True,
        extra_options=None,
    ):
        """
        This is the main method you'll probably use in your tests.

        :param Plugin plugin: plugin class or instance
        :param dict plugin_config: dict which will be used to pass options with plugin.set_options
        :param dict mock_domain: pytest fixture to mock requests to
        specific domain
        :param bool do_end_call: if False plugin.end() won't be called
        :param dict extra_options: extra options for plugin runner used in certain
        TestPluginRunner's methods.
        For example (for web_spider plugin):
            {
                'target_domain': [
                    'https://example.com/',
                    'https://example.com/somethings',
                ],
            }
        :return: Any result which returns the executed plugin. In most cases
        it's just None
        """

        if inspect.isclass(plugin):
            plugin_instance = plugin()
        else:
            plugin_instance = plugin
        self.plugin_last_ran = plugin_instance

        self.mocked_server = MockedServer(url_mapping=mock_domain)
        with NetworkPatcher(
            mock_domain,
            mocked_server=self.mocked_server,
            plugin_instance=plugin_instance,
        ):
            if plugin_config:
                self.set_options_to_plugin(plugin_instance, plugin_config)

            result = None
            did_plugin_run = False

            if isinstance(plugin_instance, AuthPlugin):
                result = run_auth_plugin(plugin_instance)
                did_plugin_run = True
            if isinstance(plugin_instance, CrawlPlugin):
                result = run_crawl_plugin(plugin_instance, extra_options)
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


def run_auth_plugin(plugin):
    if not plugin.has_active_session():
        return plugin.login()
    return False


def run_crawl_plugin(plugin_instance, extra_options=None):
    extra_options = extra_options or {}
    initial_request_url = URL('http://example.com/')
    initial_request = FuzzableRequest(initial_request_url)
    requests_to_crawl = [initial_request]
    if extra_options.get('target_domain'):
        requests_to_crawl += [
            FuzzableRequest(URL(url))
            for url in
            extra_options['target_domain']
        ]
    plugin_instance.crawl(initial_request, debugging_id='test')
    while requests_to_crawl:
        request = requests_to_crawl.pop()
        if request == POISON_PILL:
            break
        plugin_instance.crawl(request, debugging_id=MagicMock())
        for _ in range(plugin_instance.output_queue.qsize()):
            request = plugin_instance.output_queue.get(block=True)
            kb.kb.add_fuzzable_request(request)
            requests_to_crawl.append(request)
    return True


class MockedServer:
    """
    This is class used to mock whole network for TestPluginRunner. It provides
    `mock_GET` and `mock_chrome_load_url` which are methods to monkey-patch
    the real w3af methods.
    """
    def __init__(self, url_mapping=None):
        """
        :param dict or None url_mapping: url_mapping should be a dict with data
        formatted in following way: {'url_path': 'response_content'} or
        {request_number: 'response_content'}. So for example:
        {
          1: '<div>first response</div>',
          2: '<div>second response</div>',
          7: '<div>seventh response</div>',
          '/login/': '<input type"password">'
          '/me/': '<span>user@example.com</span>'
        }
        """
        self.url_mapping = url_mapping or {}
        self.default_content = '<html><body class="default">example.com</body></html>'
        self.response_count = 0
        self.urls_requested = []

    def mock_GET(self, url, *args, **kwargs):
        """
        Mock for all places where w3af uses extended urllib.

        :param URL or str url: w3af.core.data.parsers.doc.url.URL instance or str
        :return: w3af.core.data.url.HTTPResponse.HTTPResponse instance
        """
        url = str(url)
        return self._mocked_resp(URL(url), self.match_response(url))

    def mock_POST(self, url, *args, **kwargs):
        """
        Mock for all places where w3af uses extended urllib.

        :param URL or str url: w3af.core.data.parsers.doc.url.URL instance or str
        :return: w3af.core.data.url.HTTPResponse.HTTPResponse instance
        """
        url = str(url)
        return self._mocked_resp(URL(url), self.match_response(url))

    def mock_chrome_load_url(self, *args, **kwargs):
        def real_mock(self_, url, *args, **kwargs):
            """
            Set response content as chrome's DOM.

            :return: None
            """
            self_.chrome_conn.Page.reload()  # this enabled dom_analyzer.js
            response_content = self.match_response(url.url_string)
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

    def mock_response(self, url):
        """
        Sometimes you may need raw response content, not HTTPResponse instance.

        :return str: Raw response content (DOM) as string.
        """
        response = self.match_response(url)
        return response

    def match_response(self, url):
        """
        :param str url: string representing url like: https://example.com/test/
        :return str: the content of matched response
        """
        self.response_count += 1
        self.urls_requested.append(url)
        if self.url_mapping.get(self.response_count):
            return self.url_mapping[self.response_count]

        split_url = urlsplit(url)
        path_to_match = split_url.path
        if split_url.query:
            path_to_match += '?' + split_url.query
        if self.url_mapping.get(path_to_match):
            return self.url_mapping[path_to_match]
        return self.default_content

    @staticmethod
    def _mocked_resp(url, text_resp, *args, **kwargs):
        return HTTPResponse(
            code=200,
            read=text_resp,
            headers=Headers(),
            geturl=url,
            original_url=url,
        )


class NetworkPatcher:
    """
    Context manager used for mocking the whole network. It uses MockedServer
    for patching.
    """
    def __init__(self, mock_domain=None, mocked_server=None, plugin_instance=None):
        """
        :param dict mock_domain: pytest fixture to mock requests to
        specific domain
        :param MockedServer mocked_server:
        :param Plugin plugin_instance: the plugin instance
        """
        self.mock_domain = mock_domain
        self.mocked_server = mocked_server or MockedServer(url_mapping=mock_domain)
        self.plugin_instance = plugin_instance
        self.patchers = []

    def __enter__(self):
        # all non-js plugins
        patcher = patch(
            'w3af.core.data.url.extended_urllib.ExtendedUrllib.GET',
            self.mocked_server.mock_GET,
        )
        patcher.start()
        self.patchers.append(patcher)

        # all chrome (js) plugins
        chrome_patcher = patch(
            'w3af.core.controllers.chrome.instrumented.main.InstrumentedChrome.load_url',
            self.mocked_server.mock_chrome_load_url(),
        )
        chrome_patcher.start()
        self.patchers.append(chrome_patcher)

        post_patcher = patch(
            'w3af.core.data.url.extended_urllib.ExtendedUrllib.POST',
            self.mocked_server.mock_POST,
        )
        self.patchers.append(post_patcher)
        post_patcher.start()

        from w3af.plugins.crawl.web_spider import web_spider
        if self.plugin_instance and isinstance(self.plugin_instance, web_spider):
            self._handle_web_spider_plugin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for patcher in self.patchers:
            try:
                patcher.stop()
            except RuntimeError:
                pass
        return False

    def _handle_web_spider_plugin(self):
        from w3af.core.controllers.core_helpers.fingerprint_404 import fingerprint_404_singleton
        self.plugin_instance._target_domain = 'example.com'
        self.plugin_instance._first_run = False
        mocked_404_singleton = fingerprint_404_singleton(cleanup=True)
        mocked_404_singleton.set_url_opener(ExtendedUrllib())
        self.plugin_instance.set_url_opener(ExtendedUrllib())
        from w3af.core.controllers.threads.threadpool import Pool
        self.plugin_instance.set_worker_pool(Pool())


def patch_network(func):
    """
    NetworkPatcher decorator
    """
    def decorating_function(*args, **kwargs):
        with NetworkPatcher():
            return func(*args, **kwargs)
    return decorating_function
