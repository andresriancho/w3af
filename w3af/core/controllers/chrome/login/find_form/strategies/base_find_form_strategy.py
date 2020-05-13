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

    def find_forms(self):
        raise NotImplementedError

    @staticmethod
    def get_name():
        return 'BaseFindFormStrategy'
