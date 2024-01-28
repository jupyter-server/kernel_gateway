# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Entrypoint for the kernel gateway package."""
from ._version import __version__, version_info  # noqa: F401
from .gatewayapp import launch_instance  # noqa: F401
