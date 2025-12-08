"""
my_xss_test.py

A simple audit plugin example to detect reflected XSS.
"""

from w3af.core.controllers.plugins.audit_plugin import AuditPlugin
from w3af.core.data.fuzzer.fuzzer import create_mutants
from w3af.core.data.kb.vuln import Vuln


class my_xss_test(AuditPlugin):

    def __init__(self):
        super().__init__()

        # Payload you want to test with
        self.payload = "<xss123>"

    def audit(self, freq, orig_response, debugging_id):
        """
        Main audit method. Creates mutants and tests each.
        """
        mutants = create_mutants(freq, [self.payload])

        self._send_mutants_in_threads(
            func=self._check_xss,
            iterable=mutants,
            callback=lambda x, y: None
        )

    def _check_xss(self, mutant):
        """
        Check if the payload is reflected in the response.
        """
        response = self._uri_opener.send_mutant(mutant)

        if self.payload in response.get_body():
            desc = f"Reflected XSS detected in parameter '{mutant.get_token_name()}'."
            vuln = Vuln.from_mutant(
                name="Reflected XSS",
                desc=desc,
                severity=Vuln.MEDIUM,
                response_ids=[response.id],
                mutant=mutant,
            )

            self.kb_append_uniq(self, 'my_xss_test', vuln)

    def get_long_desc(self):
        return """
        This plugin is a simple example showing how to detect reflected XSS using a payload.
        """
