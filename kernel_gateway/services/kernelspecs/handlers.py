# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Tornado handlers for kernel specs."""

import jupyter_server.kernelspecs.handlers as server_kernelspecs_resources_handlers
import jupyter_server.services.kernelspecs.handlers as server_handlers

from ...mixins import CORSMixin, JSONErrorsMixin, TokenAuthorizationMixin

# Extends the default handlers from the jupyter_server package with token auth, CORS
# and JSON errors.
default_handlers = []
for path, cls in server_handlers.default_handlers:
    # Everything should have CORS and token auth
    bases = (TokenAuthorizationMixin, CORSMixin, JSONErrorsMixin, cls)
    default_handlers.append((path, type(cls.__name__, bases, {})))

for path, cls in server_kernelspecs_resources_handlers.default_handlers:
    # Everything should have CORS and token auth
    bases = (TokenAuthorizationMixin, CORSMixin, JSONErrorsMixin, cls)
    default_handlers.append((path, type(cls.__name__, bases, {})))
