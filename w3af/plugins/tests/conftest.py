import inspect

import pytest

from w3af.core.controllers.plugins.auth_plugin import AuthPlugin


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

    def run_plugin(self, plugin, plugin_config=None, mock_domain=None, do_end_call=True):
        """
        :param Plugin plugin: plugin class or instance
        :param dict plugin_config:
        :param pytest.fixture mock_domain: pytest fixture to mock requests to
        specific domain
        :param bool do_end_call: if False plugin.end() won't be called
        """
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
            plugin.end()

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


@pytest.fixture
def plugin_runner():
    """
    This fixture returns PluginRunner instance which can run the plugin inside
    sandbox environment.

    It's "core" fixture in testing w3af. 99% of time when developer wants to test
    something he runs plugin and sees what happens.
    """
    return TestPluginRunner()


@pytest.fixture
def knowledge_base():
    from w3af.core.data.kb.knowledge_base import kb
    return kb


@pytest.fixture
def js_domain_with_login_form():
    return None
