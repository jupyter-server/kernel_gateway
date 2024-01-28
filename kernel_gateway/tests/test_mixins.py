# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Tests for handler mixins."""

import json
from unittest.mock import Mock

import pytest
from tornado import web

from kernel_gateway.mixins import JSONErrorsMixin, TokenAuthorizationMixin


class SuperTokenAuthHandler:
    """Super class for the handler using TokenAuthorizationMixin."""

    is_prepared = False

    def prepare(self):
        # called by the mixin when authentication succeeds
        self.is_prepared = True


class CustomTokenAuthHandler(TokenAuthorizationMixin, SuperTokenAuthHandler):
    """Implementation that uses the TokenAuthorizationMixin for testing."""

    def __init__(self, token=""):
        self.settings = {"kg_auth_token": token}
        self.arguments = {}
        self.response = None
        self.status_code = None

    def send_error(self, status_code):
        self.status_code = status_code

    def get_argument(self, name, default=""):
        return self.arguments.get(name, default)


@pytest.fixture()
def auth_mixin():
    auth_mixin_instance = CustomTokenAuthHandler("YouKnowMe")
    return auth_mixin_instance


class TestTokenAuthMixin:
    """Unit tests the Token authorization mixin."""

    def test_no_token_required(self, auth_mixin):
        """Status should be None."""
        auth_mixin.request = Mock({})
        auth_mixin.settings["kg_auth_token"] = ""
        auth_mixin.prepare()
        assert auth_mixin.is_prepared is True
        assert auth_mixin.status_code is None

    def test_missing_token(self, auth_mixin):
        """Status should be 'unauthorized'."""
        attrs = {"headers": {}}
        auth_mixin.request = Mock(**attrs)
        auth_mixin.prepare()
        assert auth_mixin.is_prepared is False
        assert auth_mixin.status_code == 401

    def test_valid_header_token(self, auth_mixin):
        """Status should be None."""
        attrs = {"headers": {"Authorization": "token YouKnowMe"}}
        auth_mixin.request = Mock(**attrs)
        auth_mixin.prepare()
        assert auth_mixin.is_prepared is True
        assert auth_mixin.status_code is None

    def test_wrong_header_token(self, auth_mixin):
        """Status should be 'unauthorized'."""
        attrs = {"headers": {"Authorization": "token NeverHeardOf"}}
        auth_mixin.request = Mock(**attrs)
        auth_mixin.prepare()
        assert auth_mixin.is_prepared is False
        assert auth_mixin.status_code == 401

    def test_valid_url_token(self, auth_mixin):
        """Status should be None."""
        auth_mixin.arguments["token"] = "YouKnowMe"
        attrs = {"headers": {}}
        auth_mixin.request = Mock(**attrs)
        auth_mixin.prepare()
        assert auth_mixin.is_prepared is True
        assert auth_mixin.status_code is None

    def test_wrong_url_token(self, auth_mixin):
        """Status should be 'unauthorized'."""
        auth_mixin.arguments["token"] = "NeverHeardOf"
        attrs = {"headers": {}}
        auth_mixin.request = Mock(**attrs)
        auth_mixin.prepare()
        assert auth_mixin.is_prepared is False
        assert auth_mixin.status_code == 401

    def test_differing_tokens_valid_url(self, auth_mixin):
        """Status should be None, URL token takes precedence"""
        auth_mixin.arguments["token"] = "YouKnowMe"
        attrs = {"headers": {"Authorization": "token NeverHeardOf"}}
        auth_mixin.request = Mock(**attrs)
        auth_mixin.prepare()
        assert auth_mixin.is_prepared is True
        assert auth_mixin.status_code is None

    def test_differing_tokens_wrong_url(self, auth_mixin):
        """Status should be 'unauthorized', URL token takes precedence"""
        attrs = {"headers": {"Authorization": "token YouKnowMe"}}
        auth_mixin.request = Mock(**attrs)
        auth_mixin.arguments["token"] = "NeverHeardOf"
        auth_mixin.prepare()
        assert auth_mixin.is_prepared is False
        assert auth_mixin.status_code == 401

    def test_unset_client_token_with_options(self, auth_mixin):
        """No token is needed for an OPTIONS request. Enables CORS."""
        attrs = {"method": "OPTIONS"}
        auth_mixin.request = Mock(**attrs)
        auth_mixin.prepare()
        assert auth_mixin.is_prepared is True
        assert auth_mixin.status_code is None


class CustomJSONErrorsHandler(JSONErrorsMixin):
    """Implementation that uses the JSONErrorsMixin for testing."""

    def __init__(self):
        self.headers = {}
        self.response = None
        self.status_code = None
        self.reason = None

    def finish(self, response):
        self.response = response

    def set_status(self, status_code, reason=None):
        # The reason parameter is essentially ignored, but necessary in the signature
        # in order for custom messages to be returned to the client from tornado.
        # Tornado's set_status method takes both parameters setting internal members
        # to both values.  For now, we'll set the member but not use it.
        self.status_code = status_code
        self.reason = reason

    def set_header(self, name, value):
        self.headers[name] = value


@pytest.fixture()
def errors_mixin():
    errors_mixin_instance = CustomJSONErrorsHandler()
    return errors_mixin_instance


class TestJSONErrorsMixin:
    """Unit tests the JSON errors mixin."""

    def test_status(self, errors_mixin):
        """Status should be set on the response."""
        errors_mixin.write_error(404)
        response = json.loads(errors_mixin.response)
        assert errors_mixin.status_code == 404
        assert response["reason"] == "Not Found"
        assert response["message"] == ""

    def test_custom_status(self, errors_mixin):
        """Custom reason from exception should be set in the response."""
        exc = web.HTTPError(500, reason="fake-reason")
        errors_mixin.write_error(500, exc_info=[None, exc])

        response = json.loads(errors_mixin.response)
        assert errors_mixin.status_code == 500
        assert response["reason"] == "fake-reason"
        assert response["message"] == ""

    def test_log_message(self, errors_mixin):
        """Custom message from exception should be set in the response."""
        exc = web.HTTPError(410, log_message="fake-message")
        errors_mixin.write_error(410, exc_info=[None, exc])

        response = json.loads(errors_mixin.response)
        assert errors_mixin.status_code == 410
        assert response["reason"] == "Gone"
        assert response["message"] == "fake-message"
