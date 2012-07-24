from flask import Flask


class TestCase(object):
    def setup_method(self, method):
        self.app = Flask(__name__)
        self.app.debug = True
        self.app.secret_key = 'very secret'
        self._ctx = self.make_test_request_context()
        self._ctx.push()
        self.client = self.app.test_client()

    def teardown_method(self, method):
        self._ctx.pop()

    def make_test_request_context(self):
        return self.app.test_request_context()
