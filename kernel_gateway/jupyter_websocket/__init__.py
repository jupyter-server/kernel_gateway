from ..base.handlers import default_handlers as default_base_handlers
from ..services.activity.handlers import ActivityHandler
from ..services.kernels.pool import KernelPool
from ..services.kernels.handlers import default_handlers as default_kernel_handlers
from ..services.kernelspecs.handlers import default_handlers as default_kernelspec_handlers
from ..services.sessions.handlers import default_handlers as default_session_handlers
from .handlers import default_handlers as default_api_handlers
from notebook.utils import url_path_join

class JupyterWebsocketPersonality(object):
    '''Personality for standard websocket functionality, registering
    endpoints that are part of the Jupyter Kernel Gateway API
    '''
    def __init__(self, kernelspec):
        pass

    def init_configurables(self, log, options):
        """Prepares the Tornado web application with default Jupyter handlers,
        as well as the simple kernel pool.
        """
        self.log = log
        self.kernel_pool = KernelPool(
            options['prespawn_count'],
            options['kernel_manager']
        )
        self.base_url = options['base_url']

    def create_request_handlers(self):
        '''Create handlers and redefine them off of the base_url path
        '''
        handlers = []
        # append the activity monitor for websocket mode
        handlers.append((
            url_path_join('/', self.base_url, r'/_api/activity'),
            ActivityHandler,
            {}
        ))
        # append tuples for the standard kernel gateway endpoints
        for handler in (
            default_api_handlers +
            default_kernel_handlers +
            default_kernelspec_handlers +
            default_session_handlers +
            default_base_handlers
        ):
            # Create a new handler pattern rooted at the base_url
            pattern = url_path_join('/', self.base_url, handler[0])
            # Some handlers take args, so retain those in addition to the
            # handler class ref
            new_handler = tuple([pattern] + list(handler[1:]))
            handlers.append(new_handler)
        return handlers

    def should_seed_cell(self, kernel_spec, code):
        '''Determines whether the given code cell should be executed when
        seeding a new kernel.'''
        # seed all code cells
        return True

    def shutdown(self):
        """Stop all kernels in the pool."""
        self.kernel_pool.shutdown()

def create_personality(gatewayapp, kernel_name):
    return JupyterWebsocketPersonality(kernel_name)
