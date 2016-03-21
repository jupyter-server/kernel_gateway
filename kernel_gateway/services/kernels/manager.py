# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Kernel manager that optionally seeds kernel memory."""

from notebook.services.kernels.kernelmanager import MappingKernelManager
from jupyter_client.ioloop import IOLoopKernelManager
from ..cell.parser import APICellParser

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

    def start_kernel(self, *args, **kwargs):
        """Starts a kernel and then executes a list of code cells on it if a
        seed notebook exists.
        """
        kernel_id = super(MappingKernelManager, self).start_kernel(*args, **kwargs)

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
                    # Execute every non-API code cell and wait for each to
                    # succeed or fail
                    api_cell_parser = APICellParser(self.seed_kernelspec)
                    if not api_cell_parser.is_api_cell(code) and not api_cell_parser.is_api_response_cell(code):
                        client.execute(code)
                        msg = client.shell_channel.get_msg(block=True)
                        if msg['content']['status'] != 'ok':
                            # Shutdown the channels to remove any lingering ZMQ messages
                            client.stop_channels()
                            # Shutdown the kernel
                            self.shutdown_kernel(kernel_id)
                            raise RuntimeError('Error seeding kernel memory')
                # Shutdown the channels to remove any lingering ZMQ messages
                client.stop_channels()
        return kernel_id

class KernelGatewayIOLoopKernelManager(IOLoopKernelManager):
    """Extends the IOLoopKernelManagers used by the SeedingMappingKernelManager
    to include the environment variable 'KERNEL_GATEWAY' set to '1', indicating
    that the notebook is executing within a Jupyter Kernel Gateway
    """
    def _launch_kernel(self, kernel_cmd, **kw):
        kw['env']['KERNEL_GATEWAY'] = '1'
        return super(KernelGatewayIOLoopKernelManager, self)._launch_kernel(kernel_cmd, **kw)

    def is_alive(self):
        """Is the kernel process still running?"""
        if self.has_kernel:
            if self.kernel.poll() is None:
                self.has_kernel_started = True
                return True
            else:
                return False
        else:
            # we don't have a kernel
            return False

    def start_kernel(self, **kw):
        self.has_kernel_started = False
        super(KernelGatewayIOLoopKernelManager, self).start_kernel(**kw)

    def restart_kernel(self, now=False, **kw):
        """Restarts a kernel with the arguments that were used to launch it.
        If the old kernel was launched and started with random ports,
        the same ports will be used for the new kernel. The same connection
        file is used again.  If the kernel fails to start the first time
        though a new connection file will be used for the new kernel.
        Parameters
        ----------
        now : bool, optional
            If True, the kernel is forcefully restarted *immediately*, without
            having a chance to do any cleanup action.  Otherwise the kernel is
            given 1s to clean up before a forceful restart is issued.
            In all cases the kernel is restarted, the only difference is whether
            it is given a chance to perform a clean shutdown or not.
        `**kw` : optional
            Any options specified here will overwrite those used to launch the
            kernel.
        """
        if self._launch_args is None:
            raise RuntimeError("Cannot restart the kernel. "
                               "No previous call to 'start_kernel'.")
        else:
            # Stop currently running kernel.
            if self.has_kernel_started:
                self.shutdown_kernel(now=now, restart=True)
            else:
                #wipe connection file as kernel has not started at all/for the first time
                self.shutdown_kernel(now=now)

            # Start new kernel.
            self._launch_args.update(kw)
            self.start_kernel(**self._launch_args)