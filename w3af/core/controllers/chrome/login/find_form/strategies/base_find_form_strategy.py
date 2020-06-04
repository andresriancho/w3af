from w3af.core.controllers.chrome.instrumented.exceptions import EventTimeout


class BaseFindFormStrategy:
    def __init__(self, chrome, debugging_id, exact_css_selectors=None):
        """
        :param InstrumentedChrome chrome:
        :param String debugging_id:
        :param dict exact_css_selectors: Optional parameter containing css selectors
        for part of form like username input or login button.
        """
        self.chrome = chrome
        self.debugging_id = debugging_id
        self.exact_css_selectors = exact_css_selectors or {}

    def prepare(self):
        """
        :raises EventTimeout:
        Hook called before find_forms()
        """
        form_activator_selector = self.exact_css_selectors.get('form_activator')
        if form_activator_selector:
            func = 'window._DOMAnalyzer.clickOnSelector({})'.format(
                form_activator_selector
            )
            result = self.chrome.js_runtime_evaluate(func)
            if result is None:
                raise EventTimeout('The event execution timed out')

    def find_forms(self):
        raise NotImplementedError

    @staticmethod
    def get_name():
        return 'BaseFindFormStrategy'
