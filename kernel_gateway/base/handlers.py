# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Tornado handlers for the base of the API."""

import jupyter_server.base.handlers as server_handlers
from tornado import web

from ..mixins import CORSMixin, JSONErrorsMixin, TokenAuthorizationMixin


class APIVersionHandler(
    TokenAuthorizationMixin, CORSMixin, JSONErrorsMixin, server_handlers.APIVersionHandler
):
    """Extends the notebook server base API handler with token auth, CORS, and
    JSON errors.
    """


class NotFoundHandler(JSONErrorsMixin, web.RequestHandler):
    """Catches all requests and responds with 404 JSON messages.

    Installed as the fallback error for all unhandled requests.

    Raises
    ------
    tornado.web.HTTPError
        Always 404 Not Found
    """

    def prepare(self):
        raise web.HTTPError(404)


default_handlers = [(r"/api", APIVersionHandler), (r"/(.*)", NotFoundHandler)]
