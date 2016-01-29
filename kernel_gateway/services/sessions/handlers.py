# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import tornado
from notebook.base.handlers import json_errors
import notebook.services.sessions.handlers as notebook_handlers
from ...mixins import TokenAuthorizationMixin, CORSMixin

class SessionRootHandler(TokenAuthorizationMixin, 
                        CORSMixin, 
                        notebook_handlers.SessionRootHandler):
    @json_errors
    def get(self):
        '''
        Denies returning a list of running sessions  unless explicitly
        enabled, instead returning a 403 error indicating that the list is 
        permanently forbidden.
        '''
        if 'kg_list_kernels' not in self.settings or self.settings['kg_list_kernels'] != True:
            raise tornado.web.HTTPError(403, 'Forbidden')
        else:
            super(SessionRootHandler, self).get()

default_handlers = []
for path, cls in notebook_handlers.default_handlers:
    if cls.__name__ in globals():
        # Use the same named class from here if it exists
        default_handlers.append((path, globals()[cls.__name__]))
    else:
        # Everything should have CORS and token auth
        bases = (TokenAuthorizationMixin, CORSMixin, cls)
        default_handlers.append((path, type(cls.__name__, bases, {})))
