# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Tornado handlers for session CRUD."""

import jupyter_server.services.sessions.handlers as server_handlers
import tornado

from ...mixins import CORSMixin, JSONErrorsMixin, TokenAuthorizationMixin


class SessionRootHandler(
    TokenAuthorizationMixin, CORSMixin, JSONErrorsMixin, server_handlers.SessionRootHandler
):
    """Extends the notebook root session handler with token auth, CORS, and
    JSON errors.
    """

    async def get(self):
        """Overrides the super class method to honor the kernel listing
        configuration setting.

        Raises
        ------
        tornado.web.HTTPError
            If kg_list_kernels is False, respond with 403 Forbidden
        """
        if "kg_list_kernels" not in self.settings or self.settings["kg_list_kernels"] is not True:
            raise tornado.web.HTTPError(403, "Forbidden")
        else:
            await super().get()


class SessionHandler(TokenAuthorizationMixin,
                    CORSMixin,
                    JSONErrorsMixin,
                    notebook_handlers.SessionHandler):
    """Extends the notebook session handler with token auth, CORS, and
    JSON errors.
    """
    def set_default_headers(self):
        self.set_header('Content-Type', 'application/json')
        self.set_header('Access-Control-Allow-Origin', self.settings['kg_allow_origin'])
        self.set_header('Access-Control-Allow-Headers', self.settings['kg_allow_headers'])
        self.set_header('Access-Control-Allow-Methods', self.settings['kg_allow_methods'])

    def options(self, **kwargs):
        """Method for properly handling CORS pre-flight"""
        self.finish()

default_handlers = []
for path, cls in server_handlers.default_handlers:
    if cls.__name__ in globals():
        # Use the same named class from here if it exists
        default_handlers.append((path, globals()[cls.__name__]))
    else:
        # Everything should have CORS and token auth
        bases = (TokenAuthorizationMixin, CORSMixin, cls)
        default_handlers.append((path, type(cls.__name__, bases, {})))
