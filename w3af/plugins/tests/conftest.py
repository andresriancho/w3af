import pytest

from w3af.core.controllers.plugins.auth_plugin import AuthPlugin


class TestPluginError(Exception):
    pass


class TestPluginRunner:
    pass


@pytest.fixture
def set_options_to_plugin():
    def _set_options_to_plugin(plugin, options):
        """
        :param Plugin plugin: the plugin instance
        :param dict options: dict of options that will be set to plugin
        """
        options_list = plugin.get_options()
        for option_name, option_value in options.items():
            option = options_list[option_name]
            option.set_value(option_value)
        plugin.set_options(options_list)
    return _set_options_to_plugin


@pytest.fixture
def run_plugin(set_options_to_plugin):
    """
    This fixture mocks everything needed to run w3af plugin, provides special
    mocking (like mock_domain) and returns function which runs the plugin
    inside sandbox environment.

    It's "core" fixture in testing w3af. 99% of time when developer wants to test
    something he runs plugin and sees what happens.
    """
    def run_auth_plugin(plugin):
        if not plugin.has_active_session():
            plugin.login()
        plugin.end()

    def prepare_plugin(plugin_class, plugin_config):
        plugin = plugin_class()
        set_options_to_plugin(plugin, plugin_config)
        return plugin

    def execute(plugin_class, plugin_config, mock_domain=None):
        """
        :param Plugin plugin_class:
        :param dict plugin_config:
        :param pytest.fixture mock_domain: pytest fixture to mock requests to
        specific domain
        :returns Plugin: plugin instance created during run.
        """
        plugin = prepare_plugin(plugin_class, plugin_config)
        if isinstance(plugin, AuthPlugin):
            return run_auth_plugin(plugin)
        raise TestPluginError(
            "Can't find any way to run plugin {}. Is it already implemented?".format(
                plugin_class
            )
        )
    return execute


@pytest.fixture
def knowledge_base():
    from w3af.core.data.kb.knowledge_base import DBKnowledgeBase
    return DBKnowledgeBase()


@pytest.fixture
def js_domain_with_login_form():
    return None
