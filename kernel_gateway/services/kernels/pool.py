# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from tornado.locks import Semaphore
from tornado import gen

class KernelPool(object):
    '''
    Spawns a pool of kernels and cleans them up when shut down.
    '''
    def __init__(self, prespawn_count, kernel_manager):
        self.kernel_manager = kernel_manager
        # Make sure we've got a int
        if not prespawn_count:
            prespawn_count = 0
        for _ in range(prespawn_count):
            self.kernel_manager.start_seeded_kernel()

    def shutdown(self):
        kids = self.kernel_manager.list_kernel_ids()
        for kid in kids:
            self.kernel_manager.shutdown_kernel(kid, now=True)

class ManagedKernelPool(KernelPool):
    '''
    Spawns a pool of kernels. Manages access to individual kernels using a
    borrower/lender pattern. Cleans them all up when shut down.
    '''
    def __init__(self, prespawn_count, kernel_manager):
        # Make sure there's at least one kernel as a delegate
        if not prespawn_count:
            prespawn_count = 1

        super(ManagedKernelPool, self).__init__(prespawn_count, kernel_manager)

        self.kernel_clients = {}
        self.on_recv_funcs = {}
        self.pool_index = 0
        self.kernel_pool = []

        kernel_ids = self.kernel_manager.list_kernel_ids()
        self.kernel_semaphore = Semaphore(len(kernel_ids))

        # Connect to any prespawned kernels
        for kernel_id in kernel_ids:
            self.kernel_clients[kernel_id] = kernel_manager.get_kernel(kernel_id).client()
            self.kernel_pool.append(kernel_id)
            iopub = self.kernel_manager.connect_iopub(kernel_id)
            iopub.on_recv(self.create_on_reply(kernel_id))

    @gen.coroutine
    def acquire(self):
        '''
        Returns a kernel client and id for use and removes the kernel the resource pool.
        Kernels must be returned via the release method.
        :return: Returns a kernel client and a kernel id
        '''
        yield self.kernel_semaphore.acquire()
        kernel_id = self.kernel_pool[0]
        del self.kernel_pool[0]
        raise gen.Return((self.kernel_clients[kernel_id], kernel_id))

    def release(self, kernel_id):
        '''
        Returns a kernel back to the resource pool.
        :param kernel_id: Id of the kernel to return to the pool
        '''
        self.kernel_pool.append(kernel_id)
        self.kernel_semaphore.release()

    def _on_reply(self, kernel_id, msg_list):
        idents, msg_list = self.kernel_clients[kernel_id].session.feed_identities(msg_list)
        msg = self.kernel_clients[kernel_id].session.deserialize(msg_list)
        self.on_recv_funcs[kernel_id](msg)

    def create_on_reply(self, kernel_id):
        '''
        The lambda is used to handle a specific reply per kernel and provide a unique stack scope per invocation.
        '''
        return lambda msg_list: self._on_reply(kernel_id, msg_list)

    def on_recv(self, kernel_id, func):
        '''
        Registers a callback for io_pub messages for a particular kernel.
        This is needed to avoid having multiple callbacks per kernel client.
        :param kernel_id: Id of the kernel
        :param func: Callback function to handle the message
        '''
        self.on_recv_funcs[kernel_id] = func

    def shutdown(self):
        '''
        Shuts down all kernels in the pool and in the kernel manager.
        '''
        for kid in self.kernel_clients:
            self.kernel_clients[kid].stop_channels()
            self.kernel_manager.shutdown_kernel(kid, now=True)

        # Any remaining kernels that were not created for our pool should be shutdown
        super(ManagedKernelPool, self).shutdown()
