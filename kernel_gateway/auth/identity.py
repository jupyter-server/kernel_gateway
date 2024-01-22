# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Gateway Identity Provider interface

This defines the _authentication_ layer of Jupyter Server,
to be used in combination with Authorizer for _authorization_.
"""
from jupyter_server.auth.identity import IdentityProvider, User
from jupyter_server.base.handlers import JupyterHandler
from tornado import web
from traitlets import default


class GatewayIdentityProvider(IdentityProvider):
    """
    Interface for providing identity management and authentication for a Gateway server.
    """

    @default("token")
    def _token_default(self):
        return self.parent.auth_token

    @property
    def auth_enabled(self):
        if not self.token:
            return False
        return True

    def should_check_origin(self, handler: JupyterHandler) -> bool:
        """Should the Handler check for CORS origin validation?

        Origin check should be skipped for token-authenticated requests.

        Returns:
        - True, if Handler must check for valid CORS origin.
        - False, if Handler should skip origin check since requests are token-authenticated.
        """
        # Always check the origin unless operator configured gateway to allow any
        return handler.settings["kg_allow_origin"] != "*"

    def generate_anonymous_user(self, handler: web.RequestHandler) -> User:
        """Generate a random anonymous user.

        For use when a single shared token is used,
        but does not identify a user.
        """
        name = display_name = "Anonymous"
        initials = "An"
        color = None
        return User(name.lower(), name, display_name, initials, None, color)

    def is_token_authenticated(self, handler: web.RequestHandler) -> bool:
        """The default authentication flow of Gateway is token auth.

        The only other option is no auth
        """
        return True
