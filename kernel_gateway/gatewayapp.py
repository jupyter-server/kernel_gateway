# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Kernel Gateway Jupyter application."""

import os
import socket
import errno
import logging
import nbformat
import importlib

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

from traitlets import Unicode, Integer, Bool, default

from jupyter_core.application import JupyterApp
from jupyter_client.kernelspec import KernelSpecManager

# Install the pyzmq ioloop. This has to be done before anything else from
# tornado is imported.
from zmq.eventloop import ioloop
ioloop.install()

from tornado import httpserver
from tornado import web
from tornado.log import enable_pretty_logging

from notebook.notebookapp import random_ports
from .services.sessions.sessionmanager import SessionManager
from .services.activity.manager import ActivityManager
from .services.kernels.manager import SeedingMappingKernelManager

class KernelGatewayApp(JupyterApp):
    """Application that provisions Jupyter kernels and proxies HTTP/Websocket
    traffic to the kernels.

    - reads command line and environment variable settings
    - initializes managers and routes
    - creates a Tornado HTTP server
    - starts the Tornado event loop
    """
    name = 'jupyter-kernel-gateway'
    description = """
        Jupyter Kernel Gateway

        Provisions Jupyter kernels and proxies HTTP/Websocket traffic
        to them.
    """
    # Server IP / PORT binding
    port_env = 'KG_PORT'
    port = Integer(config=True,
        help="Port on which to listen (KG_PORT env var)"
    )
    @default('port')
    def port_default(self):
        return int(os.getenv(self.port_env, 8888))
    
    port_retries_env = 'KG_PORT_RETRIES'
    port_retries = Integer(config=True,
        help="Number of ports to try if the specified port is not available (KG_PORT_RETRIES env var)"
    )
    @default('port_retries')
    def port_retries_default(self):
        return int(os.getenv(self.port_retries_env, 50))

    ip_env = 'KG_IP'
    ip = Unicode(config=True,
        help="IP address on which to listen (KG_IP env var)"
    )
    @default('ip')
    def ip_default(self):
        return os.getenv(self.ip_env, '127.0.0.1')

    # Base URL
    base_url_env = 'KG_BASE_URL'
    base_url = Unicode(config=True,
        help="""The base path for mounting all API resources (KG_BASE_URL env var)""")
    @default('base_url')
    def base_url_default(self):
        return os.getenv(self.base_url_env, '/')

    # Token authorization
    auth_token_env = 'KG_AUTH_TOKEN'
    auth_token = Unicode(config=True,
        help='Authorization token required for all requests (KG_AUTH_TOKEN env var)'
    )
    @default('auth_token')
    def _auth_token_default(self):
        return os.getenv(self.auth_token_env, '')

    # CORS headers
    allow_credentials_env = 'KG_ALLOW_CREDENTIALS'
    allow_credentials = Unicode(config=True,
        help='Sets the Access-Control-Allow-Credentials header. (KG_ALLOW_CREDENTIALS env var)'
    )
    @default('allow_credentials')
    def allow_credentials_default(self):
        return os.getenv(self.allow_credentials_env, '')

    allow_headers_env = 'KG_ALLOW_HEADERS'
    allow_headers = Unicode(config=True,
        help='Sets the Access-Control-Allow-Headers header. (KG_ALLOW_HEADERS env var)'
    )
    @default('allow_headers')
    def allow_headers_default(self):
        return os.getenv(self.allow_headers_env, '')

    allow_methods_env = 'KG_ALLOW_METHODS'
    allow_methods = Unicode(config=True,
        help='Sets the Access-Control-Allow-Methods header. (KG_ALLOW_METHODS env var)'
    )
    @default('allow_methods')
    def allow_methods_default(self):
        return os.getenv(self.allow_methods_env, '')

    allow_origin_env = 'KG_ALLOW_ORIGIN'
    allow_origin = Unicode(config=True,
        help='Sets the Access-Control-Allow-Origin header. (KG_ALLOW_ORIGIN env var)'
    )
    @default('allow_origin')
    def allow_origin_default(self):
        return os.getenv(self.allow_origin_env, '')

    expose_headers_env = 'KG_EXPOSE_HEADERS'
    expose_headers = Unicode(config=True,
        help='Sets the Access-Control-Expose-Headers header. (KG_EXPOSE_HEADERS env var)'
    )
    @default('expose_headers')
    def expose_headers_default(self):
        return os.getenv(self.expose_headers_env, '')

    max_age_env = 'KG_MAX_AGE'
    max_age = Unicode(config=True,
        help='Sets the Access-Control-Max-Age header. (KG_MAX_AGE env var)'
    )
    @default('max_age')
    def max_age_default(self):
        return os.getenv(self.max_age_env, '')

    max_kernels_env = 'KG_MAX_KERNELS'
    max_kernels = Integer(config=True,
        allow_none=True,
        help='Limits the number of kernel instances allowed to run by this gateway. (KG_MAX_KERNELS env var)'
    )
    @default('max_kernels')
    def max_kernels_default(self):
        val = os.getenv(self.max_kernels_env)
        return val if val is None else int(val)

    seed_uri_env = 'KG_SEED_URI'
    seed_uri = Unicode(config=True,
        allow_none=True,
        help='Runs the notebook (.ipynb) at the given URI on every kernel launched. (KG_SEED_URI env var)'
    )
    @default('seed_uri')
    def seed_uri_default(self):
        return os.getenv(self.seed_uri_env)

    prespawn_count_env = 'KG_PRESPAWN_COUNT'
    prespawn_count = Integer(config=True,
        default_value=None,
        allow_none=True,
        help='Number of kernels to prespawn using the default language. (KG_PRESPAWN_COUNT env var)'
    )
    @default('prespawn_count')
    def prespawn_count_default(self):
        val = os.getenv(self.prespawn_count_env)
        return val if val is None else int(val)

    default_kernel_name_env = 'KG_DEFAULT_KERNEL_NAME'
    default_kernel_name = Unicode(config=True,
        help="""The default kernel name when spawning a kernel (KG_DEFAULT_KERNEL_NAME env var)""")
    @default('default_kernel_name')
    def default_kernel_name_default(self):
        # defaults to Jupyter's default kernel name on empty string
        return os.getenv(self.default_kernel_name_env, '')

    list_kernels_env = 'KG_LIST_KERNELS'
    list_kernels = Bool(config=True,
        help="""Permits listing of the running kernels using API endpoints /api/kernels
            and /api/sessions (KG_LIST_KERNELS env var). Note: Jupyter Notebook
            allows this by default but kernel gateway does not."""
    )
    @default('list_kernels')
    def list_kernels_default(self):
        return os.getenv(self.list_kernels_env, 'False') == 'True'

    api_env = 'KG_API'
    api = Unicode('kernel_gateway.jupyter_websocket',
        config=True,
        help='Controls which API to expose, that of a Jupyter kernel or the seed notebook\'s, using values "kernel_gateway.jupyter_websocket" or "kernel_gateway.notebook_http" (KG_API env var)'
    )
    @default('api')
    def api_default(self):
        return os.getenv(self.api_env, 'kernel_gateway.jupyter_websocket')

    def _api_changed(self, name, old, new):
        new_module = self._load_api_module(new)
        if new_module is None:
            raise ValueError('Invalid API value, module {} was not found'.format(new))

    allow_notebook_download_env = 'KG_ALLOW_NOTEBOOK_DOWNLOAD'
    allow_notebook_download = Bool(
        config=True,
        help="Optional API to download the notebook source code in notebook-http mode, defaults to not allow"
    )
    @default('allow_notebook_download')
    def allow_notebook_download_default(self):
        return os.getenv(self.allow_notebook_download_env, 'False') == 'True'

    def _load_api_module(self, module_name):
        '''Tries to import the given module name'''
        api_module = None
        # some compatibility allowances
        if module_name == 'jupyter-websocket':
            module_name = 'kernel_gateway.jupyter_websocket'
        elif module_name == 'notebook-http':
            module_name = 'kernel_gateway.notebook_http'
        api_module = importlib.import_module(module_name)
        return api_module

    def _load_notebook(self, uri):
        """Loads a notebook from the local filesystem or HTTP URL.

        Raises
        ------
        RuntimeError if no installed kernel can handle the language specified
        in the notebook.

        Returns
        -------
        object
            Notebook object from nbformat
        """
        parts = urlparse(uri)

        if parts.netloc == '' or parts.netloc == 'file':
            # Local file
            with open(parts.path) as nb_fh:
                notebook = nbformat.read(nb_fh, 4)
        else:
            # Remote file
            import requests
            resp = requests.get(uri)
            resp.raise_for_status()
            notebook = nbformat.reads(resp.text, 4)

        # Error if no kernel spec can handle the language requested
        kernel_name = notebook['metadata']['kernelspec']['name']
        self.kernel_spec_manager.get_kernel_spec(kernel_name)

        return notebook

    def initialize(self, argv=None):
        """Initializes the base class, configurable manager instances, the
        Tornado web app, and the tornado HTTP server.

        Parameters
        ----------
        argv
            Command line arguments
        """
        super(KernelGatewayApp, self).initialize(argv)
        self.init_configurables()
        self.init_webapp()
        self.init_http_server()

    def init_configurables(self):
        """Initializes all configurable objects including a kernel manager, kernel
        spec manager, session manager, activity manager, and personality.

        Any kernel pool configured by the personality will be its responsibility
        to shut down.

        Optionally, loads a notebook and prespawns the configured number of
        kernels.
        """
        self.kernel_spec_manager = KernelSpecManager(parent=self)

        self.seed_notebook = None
        if self.seed_uri is not None:
            # Note: must be set before instantiating a SeedingMappingKernelManager
            self.seed_notebook = self._load_notebook(self.seed_uri)

        # Only pass a default kernel name when one is provided. Otherwise,
        # adopt whatever default the kernel manager wants to use.
        kwargs = {}
        if self.default_kernel_name:
            kwargs['default_kernel_name'] = self.default_kernel_name
        self.kernel_manager = SeedingMappingKernelManager(
            parent=self,
            log=self.log,
            connection_dir=self.runtime_dir,
            kernel_spec_manager=self.kernel_spec_manager,
            **kwargs
        )

        self.activity_manager = ActivityManager(
            parent=self,
            log=self.log,
            kernel_manager=self.kernel_manager
        )

        self.session_manager = SessionManager(
            log=self.log,
            kernel_manager=self.kernel_manager
        )
        self.contents_manager = None

        if self.prespawn_count:
            if self.max_kernels and self.prespawn_count > self.max_kernels:
                raise RuntimeError('cannot prespawn {}; more than max kernels {}'.format(
                    self.prespawn_count, self.max_kernels)
                )

        api_module = self._load_api_module(self.api)
        func = getattr(api_module, 'create_personality')
        self.personality = func(self)

        self.personality.init_configurables(self)

    def init_webapp(self):
        """Initializes Tornado web application with uri handlers.

        Adds the various managers and web-front configuration values to the
        Tornado settings for reference by the handlers.

        Notes
        -----
        Uses the `api` setting to determine which handlers to add.
        Developers should note: this may be refactored in the future.
        """
        # Enable the same pretty logging the notebook uses
        enable_pretty_logging()

        # Configure the tornado logging level too
        logging.getLogger().setLevel(self.log_level)

        handlers = self.personality.create_request_handlers()

        self.web_app = web.Application(
            handlers=handlers,
            activity_manager=self.activity_manager,
            kernel_manager=self.kernel_manager,
            session_manager=self.session_manager,
            contents_manager=self.contents_manager,
            kernel_spec_manager=self.kernel_manager.kernel_spec_manager,
            kg_auth_token=self.auth_token,
            kg_allow_credentials=self.allow_credentials,
            kg_allow_headers=self.allow_headers,
            kg_allow_methods=self.allow_methods,
            kg_allow_origin=self.allow_origin,
            kg_expose_headers=self.expose_headers,
            kg_max_age=self.max_age,
            kg_max_kernels=self.max_kernels,
            kg_list_kernels=self.list_kernels,
            kg_api=self.api,
            # Also set the allow_origin setting used by notebook so that the
            # check_origin method used everywhere respects the value
            allow_origin=self.allow_origin
        )

    def init_http_server(self):
        """Initializes a HTTP server for the Tornado web application on the
        configured interface and port.
        
        Tries to find an open port if the one configured is not available using
        the same logic as the Jupyer Notebook server.
        """
        self.http_server = httpserver.HTTPServer(self.web_app)
        
        for port in random_ports(self.port, self.port_retries+1):
            try:
                self.http_server.listen(port, self.ip)
            except socket.error as e:
                if e.errno == errno.EADDRINUSE:
                    self.log.info('The port %i is already in use, trying another port.' % port)
                    continue
                elif e.errno in (errno.EACCES, getattr(errno, 'WSAEACCES', errno.EACCES)):
                    self.log.warning("Permission to listen on port %i denied" % port)
                    continue
                else:
                    raise
            else:
                self.port = port
                break
        else:
            self.log.critical('ERROR: the notebook server could not be started because '
                              'no available port could be found.')
            self.exit(1)

    def start(self):
        """Starts an IO loop for the application."""
        super(KernelGatewayApp, self).start()
        self.log.info('The Jupyter Kernel Gateway is running at: http://{}:{}'.format(
            self.ip, self.port
        ))

        self.io_loop = ioloop.IOLoop.current()

        try:
            self.io_loop.start()
        except KeyboardInterrupt:
            self.log.info("Interrupted...")

    def stop(self):
        """
        Stops the HTTP server and IO loop associated with the application.
        """
        def _stop():
            self.http_server.stop()
            self.io_loop.stop()
        self.io_loop.add_callback(_stop)

    def shutdown(self):
        """Stop all kernels in the pool."""
        self.personality.shutdown()

launch_instance = KernelGatewayApp.launch_instance
