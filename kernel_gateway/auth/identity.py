# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Gateway Identity Provider interface

This defines the _authentication_ layer of Jupyter Server,
to be used in combination with Authorizer for _authorization_.
"""
from traitlets import default

from jupyter_server.auth.identity import IdentityProvider
from jupyter_server.base.handlers import JupyterHandler


class GatewayIdentityProvider(IdentityProvider):
    """
    Interface for providing identity management and authentication for a Gateway server.
    """
    @default("token")
    def _token_default(self):
        # if the superclass generated a token, but auth_token is configured on
        # the Gateway server, reset token_generated and use the configured value.
        token_default = super()._token_default()
        if self.token_generated and self.parent.auth_token:
            self.token_generated = False
            return self.parent.auth_token
        return token_default

    def should_check_origin(self, handler: JupyterHandler) -> bool:
        """Should the Handler check for CORS origin validation?

        Origin check should be skipped for token-authenticated requests.

        Returns:
        - True, if Handler must check for valid CORS origin.
        - False, if Handler should skip origin check since requests are token-authenticated.
        """
        # Always check the origin unless operator configured gateway to allow any
        return handler.settings["kg_allow_origin"] != "*"
