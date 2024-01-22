# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Kernel pools that track and delegate to kernels."""

import asyncio
from typing import Awaitable, List, Optional

from jupyter_client.session import Session
from jupyter_server.services.kernels.kernelmanager import MappingKernelManager
from tornado.concurrent import Future
from tornado.locks import Semaphore
from traitlets.config.configurable import LoggingConfigurable


class KernelPool(LoggingConfigurable):
    """Spawns a pool of kernels.

    The kernel pool is responsible for clean up and shutdown of individual
    kernels that are members of the pool.

    Parameters
    ----------
    prespawn_count
        Number of kernels to spawn immediately
    kernel_manager
        Kernel manager instance
    """

    kernel_manager: Optional[MappingKernelManager]
    pool_initialized: Future

    def __init__(self):
        super().__init__()
        self.kernel_manager = None
        self.pool_initialized = Future()

    async def initialize(self, prespawn_count, kernel_manager, **kwargs):
        self.kernel_manager = kernel_manager
        # Make sure we've got a int
        if not prespawn_count:
            prespawn_count = 0

        kernels_to_spawn: List[Awaitable] = []
        for _ in range(prespawn_count):
            kernels_to_spawn.append(self.kernel_manager.start_seeded_kernel())

        await asyncio.gather(*kernels_to_spawn)

        # Indicate that pool initialization has completed
        self.pool_initialized.set_result(True)

    async def shutdown(self):
        """Shuts down all running kernels."""
        await self.pool_initialized
        kids = self.kernel_manager.list_kernel_ids()
        for kid in kids:
            await self.kernel_manager.shutdown_kernel(kid, now=True)


class ManagedKernelPool(KernelPool):
    """Spawns a pool of kernels that are treated as identical delegates for
    future requests.

    Manages access to individual kernels using a borrower/lender pattern.
    Cleans them all up when shut down.

    Parameters
    ----------
    prespawn_count
        Number of kernels to spawn immediately
    kernel_manager
        Kernel manager instance

    Attributes
    ----------
    kernel_clients : dict
        Map of kernel IDs to client instances for communicating with them
    on_recv_funcs : dict
        Map of kernel IDs to iopub callback functions
    kernel_pool : list
        List of available delegate kernel IDs
    kernel_semaphore : tornado.locks.Semaphore
        Semaphore that controls access to the kernel pool
    """

    kernel_clients: dict
    on_recv_funcs: dict
    kernel_pool: list
    kernel_semaphore: Semaphore
    managed_pool_initialized: Future

    def __init__(self):
        super().__init__()
        self.kernel_clients = {}
        self.on_recv_funcs = {}
        self.kernel_pool = []
        self.managed_pool_initialized = Future()

    async def initialize(self, prespawn_count, kernel_manager, **kwargs):
        # Make sure there's at least one kernel as a delegate
        if not prespawn_count:
            prespawn_count = 1

        self.kernel_semaphore = Semaphore(prespawn_count)

        await super().initialize(prespawn_count, kernel_manager)

        kernel_ids = self.kernel_manager.list_kernel_ids()

        # Create clients and iopub handlers for prespawned kernels
        for kernel_id in kernel_ids:
            self.kernel_clients[kernel_id] = kernel_manager.get_kernel(kernel_id).client()
            self.kernel_pool.append(kernel_id)
            iopub = self.kernel_manager.connect_iopub(kernel_id)
            iopub.on_recv(self.create_on_reply(kernel_id))

        # Indicate that pool initialization has completed
        self.managed_pool_initialized.set_result(True)

    async def acquire(self):
        """Gets a kernel client and removes it from the available pool of
        clients.

        Returns
        -------
        tuple
            Kernel client instance, kernel ID
        """
        await self.managed_pool_initialized
        await self.kernel_semaphore.acquire()
        kernel_id = self.kernel_pool[0]
        del self.kernel_pool[0]
        return self.kernel_clients[kernel_id], kernel_id

    def release(self, kernel_id):
        """Puts a kernel back into the pool of kernels available to handle
        requests.

        Parameters
        ----------
        kernel_id : str
            Kernel to return to the pool
        """
        self.kernel_pool.append(kernel_id)
        self.kernel_semaphore.release()

    def _on_reply(self, kernel_id, session, msg_list):
        """Invokes the iopub callback registered for the `kernel_id` and passes
        it a deserialized list of kernel messages.

        Parameters
        ----------
        kernel_id : str
            Kernel that sent the reply
        msg_list : list
            List of 0mq messages
        """
        if kernel_id not in self.on_recv_funcs:
            self.log.warning(f"Could not find callback for kernel_id: {kernel_id}")
            return
        idents, msg_list = session.feed_identities(msg_list)
        msg = session.deserialize(msg_list)
        self.on_recv_funcs[kernel_id](msg)

    def create_on_reply(self, kernel_id):
        """Creates an anonymous function to handle reply messages from the
        kernel.

        Parameters
        ----------
        kernel_id
            Kernel to listen to

        Returns
        -------
        function
            Callback function taking a kernel ID and 0mq message list
        """
        kernel = self.kernel_clients[kernel_id]
        session = Session(
            config=kernel.session.config,
            key=kernel.session.key,
        )
        return lambda msg_list: self._on_reply(kernel_id, session, msg_list)

    def on_recv(self, kernel_id, func):
        """Registers a callback function for iopub messages from a particular
        kernel.

        This is needed to avoid having multiple callbacks per kernel client.

        Parameters
        ----------
        kernel_id
            Kernel from which to receive iopub messages
        func
            Callback function to use for kernel iopub messages
        """
        self.on_recv_funcs[kernel_id] = func

    async def shutdown(self):
        """Shuts down all kernels and their clients."""
        await self.managed_pool_initialized
        for kid in self.kernel_clients:
            self.kernel_clients[kid].stop_channels()
            await self.kernel_manager.shutdown_kernel(kid, now=True)

        # Any remaining kernels that were not created for our pool should be shutdown
        await super().shutdown()
