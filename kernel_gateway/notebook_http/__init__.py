from ..base.handlers import default_handlers as default_base_handlers
from ..services.kernels.pool import ManagedKernelPool
from .cell.parser import APICellParser
from .swagger.handlers import SwaggerSpecHandler
from .handlers import NotebookAPIHandler, parameterize_path, NotebookDownloadHandler
from notebook.utils import url_path_join

class NotebookHTTPPersonality(object):
    '''Personality for notebook-http support, creating REST endpoints
    based on the notebook's cells
    '''
    def __init__(self, kernelspec):
        self.api_parser = APICellParser(kernelspec)

    def init_configurables(self, log, options):
        """Prepares the Tornado web application with any needed handlers, as
        well as the stateless kernel pool.
        """
        self.log = log
        self.kernel_pool = ManagedKernelPool(
            options['prespawn_count'],
            options['kernel_manager']
        )
        self.kernel_manager = options['kernel_manager']
        self.base_url = options['base_url']
        self.seed_uri = options['seed_uri']
        self.allow_notebook_download = options['allow_notebook_download']

    def create_request_handlers(self):
        '''Create handlers and redefine them off of the base_url path. Assumes
        init_configurables() has been called with a kernel_manager, and that
        the seed source is available therein.
        '''
        handlers = []
        # Register the NotebookDownloadHandler if configuration allows
        if self.allow_notebook_download:
            handlers.append((
                url_path_join('/', self.base_url, r'/_api/source'),
                NotebookDownloadHandler,
                {'path': self.seed_uri}
            ))

        # Discover the notebook endpoints and their implementations
        endpoints = self.api_parser.endpoints(self.kernel_manager.seed_source)
        response_sources = self.api_parser.endpoint_responses(self.kernel_manager.seed_source)
        if len(endpoints) == 0:
            raise RuntimeError('No endpoints were discovered. Check your notebook to make sure your cells are annotated correctly.')

        # Cycle through the (endpoint_path, source) tuples and register their handlers
        for endpoint_path, verb_source_map in endpoints:
            parameterized_path = parameterize_path(endpoint_path)
            parameterized_path = url_path_join('/', self.base_url, parameterized_path)
            self.log.info('Registering endpoint_path: {}, methods: ({})'.format(
                parameterized_path,
                list(verb_source_map.keys())
            ))
            response_source_map = response_sources[endpoint_path] if endpoint_path in response_sources else {}
            handler_args = { 'sources' : verb_source_map,
                'response_sources' : response_source_map,
                'kernel_pool' : self.kernel_pool,
                'kernel_name' : self.kernel_manager.seed_kernelspec
            }
            handlers.append((parameterized_path, NotebookAPIHandler, handler_args))

        # Register the swagger API spec handler
        handlers.append(
            (url_path_join('/', self.base_url, r'/_api/spec/swagger.json'),
            SwaggerSpecHandler, {
                'notebook_path' : self.seed_uri,
                'source_cells': self.kernel_manager.seed_source,
                'kernel_spec' : self.kernel_manager.seed_kernelspec
        }))

        # Add the 404 catch-all last
        handlers.append(default_base_handlers[-1])
        return handlers

    def should_seed_cell(self, kernel_spec, code):
        '''Determines whether the given code cell should be executed when
        seeding a new kernel.'''
        # seed cells that are uninvolved with the presented API
        return (not self.api_parser.is_api_cell(code) and not self.api_parser.is_api_response_cell(code))

    def shutdown(self):
        """Stop all kernels in the pool."""
        self.kernel_pool.shutdown()

def create_personality(gatewayapp, kernel_name):
    return NotebookHTTPPersonality(kernel_name)
