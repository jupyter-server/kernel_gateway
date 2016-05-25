# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Kernel manager that optionally seeds kernel memory."""

from tornado import gen
from notebook.services.kernels.kernelmanager import MappingKernelManager
from jupyter_client.ioloop import IOLoopKernelManager

class SeedingMappingKernelManager(MappingKernelManager):
    """Extends the notebook kernel manager to optionally execute the contents
    of a notebook on a kernel when it starts.
    """
    def _kernel_manager_class_default(self):
        return 'kernel_gateway.services.kernels.manager.KernelGatewayIOLoopKernelManager'

    @property
    def seed_kernelspec(self):
        """Gets the kernel spec name required to run the seed notebook.

        Returns
        -------
        str
            Name of the notebook kernelspec or None if no seed notebook exists
        """
        if hasattr(self, '_seed_kernelspec'):
            return self._seed_kernelspec

        if self.parent.seed_notebook:
            self._seed_kernelspec = self.parent.seed_notebook['metadata']['kernelspec']['name']
        else:
            self._seed_kernelspec = None

        return self._seed_kernelspec

    @property
    def seed_source(self):
        """Gets the source of the seed notebook in cell order.

        Returns
        -------
        list
            Notebook code cell contents or None if no seed notebook exists
        """
        if hasattr(self, '_seed_source'):
            return self._seed_source

        if self.parent.seed_notebook:
            self._seed_source = [
                cell['source'] for cell in self.parent.seed_notebook.cells
                if cell['cell_type'] == 'code'
            ]
        else:
            self._seed_source = None

        return self._seed_source

    def start_seeded_kernel(self, *args, **kwargs):
        """Starts a kernel using the language specified in the seed notebook.

        If there is no seed notebook, start a kernel using the other parameters
        specified.
        """
        self.start_kernel(kernel_name=self.seed_kernelspec, *args, **kwargs)

    @gen.coroutine
    def start_kernel(self, *args, **kwargs):
        """Starts a kernel and then executes a list of code cells on it if a
        seed notebook exists.
        """
        kernel_id = yield gen.maybe_future(super(SeedingMappingKernelManager, self).start_kernel(*args, **kwargs))

        if kernel_id and self.seed_source is not None:
            # Only run source if the kernel spec matches the notebook kernel spec
            kernel = self.get_kernel(kernel_id)
            if kernel.kernel_name == self.seed_kernelspec:
                # Create a client to talk to the kernel
                client = kernel.client()
                # Only start channels and wait for ready in HTTP mode
                client.start_channels()
                client.wait_for_ready()
                for code in self.seed_source:
                    if self.parent.personality.should_seed_cell(self.seed_kernelspec, code):
                        client.execute(code)
                        msg = client.shell_channel.get_msg(block=True)
                        if msg['content']['status'] != 'ok':
                            # Shutdown the channels to remove any lingering ZMQ messages
                            client.stop_channels()
                            # Shutdown the kernel
                            self.shutdown_kernel(kernel_id)
                            raise RuntimeError('Error seeding kernel memory', msg['content'])
                # Shutdown the channels to remove any lingering ZMQ messages
                client.stop_channels()
        raise gen.Return(kernel_id)

class KernelGatewayIOLoopKernelManager(IOLoopKernelManager):
    """Extends the IOLoopKernelManager used by the SeedingMappingKernelManager
    to include the environment variable 'KERNEL_GATEWAY' set to '1', indicating
    that the notebook is executing within a Jupyter Kernel Gateway
    """
    def _launch_kernel(self, kernel_cmd, **kw):
        kw['env']['KERNEL_GATEWAY'] = '1'
        return super(KernelGatewayIOLoopKernelManager, self)._launch_kernel(kernel_cmd, **kw)
