# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Mixins for Tornado handlers."""

import json
import traceback
from http.client import responses

from tornado import web


class CORSMixin:
    """Mixes CORS headers into tornado.web.RequestHandlers."""

    SETTINGS_TO_HEADERS = {
        "kg_allow_credentials": "Access-Control-Allow-Credentials",
        "kg_allow_headers": "Access-Control-Allow-Headers",
        "kg_allow_methods": "Access-Control-Allow-Methods",
        "kg_allow_origin": "Access-Control-Allow-Origin",
        "kg_expose_headers": "Access-Control-Expose-Headers",
        "kg_max_age": "Access-Control-Max-Age",
    }

    def set_cors_headers(self):
        """Sets the CORS headers as the default for all responses.

        Disables CSP configured by the notebook package. It's not necessary
        for a programmatic API.

        Notes
        -----
        This method name was changed from set_default_headers to set_cors_header
        when adding support for JupyterServer 2.x.  In that release, JS changed the
        way the headers were implemented due to changes in the way a user is authenticated.
        See https://github.com/jupyter-server/jupyter_server/pull/671.
        """
        super().set_cors_headers()

        # Add CORS headers after default if they have a non-blank value
        for settings_name, header_name in self.SETTINGS_TO_HEADERS.items():
            header_value = self.settings.get(settings_name)
            if header_value:
                self.set_header(header_name, header_value)

        # Don't set CSP: we're not serving frontend media types only JSON
        self.clear_header("Content-Security-Policy")

    def options(self, *args, **kwargs):
        """Override the notebook implementation to return the headers
        configured in `set_default_headers instead of the hardcoded set
        supported by the handler base class in the notebook project.
        """
        self.finish()


class TokenAuthorizationMixin:
    """Mixes token auth into tornado.web.RequestHandlers and
    tornado.websocket.WebsocketHandlers.
    """

    header_prefix = "token "
    header_prefix_len = len(header_prefix)

    def prepare(self):
        """Ensures the correct auth token is present, either as a parameter
        `token=<value>` or as a header `Authorization: token <value>`.
        Does nothing unless an auth token is configured in kg_auth_token.

        If kg_auth_token is set and the token is not present, responds
        with 401 Unauthorized.

        Notes
        -----
        Implemented in prepare rather than in `get_user` to avoid interaction
        with the `@web.authenticated` decorated methods in the notebook
        package.
        """
        server_token = self.settings.get("kg_auth_token")
        if server_token and self.request.method != "OPTIONS":
            client_token = self.get_argument("token", None)
            if client_token is None:
                client_token = self.request.headers.get("Authorization")
                if client_token and client_token.startswith(self.header_prefix):
                    client_token = client_token[self.header_prefix_len :]
                else:
                    client_token = None
            if client_token != server_token:
                return self.send_error(401)
        return super().prepare()


class JSONErrorsMixin:
    """Mixes `write_error` into tornado.web.RequestHandlers to respond with
    JSON format errors.
    """

    def write_error(self, status_code, **kwargs):
        """Responds with an application/json error object.

        Overrides the APIHandler.write_error in the notebook server until it
        properly sets the 'reason' field.

        Parameters
        ----------
        status_code
            HTTP status code to set
        **kwargs
            Arbitrary keyword args. Only uses `exc_info[1]`, if it exists,
            to get a `log_message`, `args`, and `reason` from a raised
            exception that triggered this method

        Examples
        --------
        {"401", reason="Unauthorized", message="Invalid auth token"}
        """
        exc_info = kwargs.get("exc_info")
        message = ""
        reason = responses.get(status_code, "Unknown HTTP Error")
        reply = {
            "reason": reason,
            "message": message,
        }
        if exc_info:
            exception = exc_info[1]
            # Get the custom message, if defined
            if isinstance(exception, web.HTTPError):
                reply["message"] = exception.log_message or message
            else:
                reply["message"] = "Unknown server error"
                reply["traceback"] = "".join(traceback.format_exception(*exc_info))

            # Construct the custom reason, if defined
            custom_reason = getattr(exception, "reason", "")
            if custom_reason:
                reply["reason"] = custom_reason

        self.set_header("Content-Type", "application/json")
        self.set_status(status_code, reason=reply["reason"])
        self.finish(json.dumps(reply))
