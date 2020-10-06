import pytest

from w3af.plugins.tests.plugin_testing_tools import TestPluginRunner


def cleanup_parser_cache():
    from w3af.core.data.parsers import parser_cache
    parser_cache.dpc = parser_cache.ParserCache()


@pytest.fixture
def plugin_runner():
    """
    This fixture returns PluginRunner instance which can run the plugin inside
    sandbox environment.

    It's "core" fixture in testing w3af. 99% of time when developer wants to test
    something he runs plugin and sees what happens.
    """
    cleanup_parser_cache()
    return TestPluginRunner()


@pytest.fixture
def js_domain_with_login_form():
    mapping = {
        1: '<div>example</div>',
        '/login/': (
            '<div>'
            '<input id="username"></input>'
            '<input type="password"></input>'
            '<button id="login">login</button>'
            '</div>'
        ),
        '/me/': '<div>logged as</div>',
    }
    return mapping


@pytest.fixture
def knowledge_base():
    from w3af.core.data.kb import knowledge_base
    kb = knowledge_base.kb = knowledge_base.DBKnowledgeBase()  # create new kb instance
    return kb
