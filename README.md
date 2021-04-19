# Jupyter Kernel Gateway

[![Google Group](https://img.shields.io/badge/-Google%20Group-lightgrey.svg)](https://groups.google.com/forum/#!forum/jupyter) 
[![PyPI version](https://badge.fury.io/py/jupyter_kernel_gateway.svg)](https://badge.fury.io/py/jupyter_kernel_gateway)
[![Build Status](https://github.com/jupyter/kernel_gateway/workflows/Tests/badge.svg)](https://github.com/jupyter/kernel_gateway/actions?query=workflow%3ATests)
[![Documentation Status](http://readthedocs.org/projects/jupyter-kernel-gateway/badge/?version=latest)](https://jupyter-kernel-gateway.readthedocs.io/en/latest/?badge=latest)

## Overview

Jupyter Kernel Gateway is a web server that provides headless access to
Jupyter kernels. Your application communicates with the kernels remotely,
through REST calls and Websockets rather than ZeroMQ messages.
There are no provisions for editing notebooks through the Kernel Gateway.
The following operation modes, called personalities, are supported
out of the box:

* Send code snippets for execution using the
  [Jupyter kernel protocol](https://jupyter-client.readthedocs.io/en/latest/messaging.html)
  over Websockets. Start and stop kernels through REST calls.
  This HTTP API is compatible with the respective API sections
  of the Jupyter Notebook server.

* Serve HTTP requests from annotated notebook cells. The code snippets
  are cells of a static notebook configured in the Kernel Gateway.
  Annotations define which HTTP verbs and resources it supports.
  Incoming requests are served by executing one of the cells in a kernel.

Jupyter Kernel Gateway uses the same code as Jupyter Notebook
to launch kernels in its local process/filesystem space.
It can be containerized and scaled out using common technologies like [tmpnb](https://github.com/jupyter/tmpnb), [Cloud Foundry](https://github.com/cloudfoundry), and [Kubernetes](http://kubernetes.io/).

### Example Uses of Kernel Gateway

* Attach a local Jupyter Notebook server to a compute cluster in the cloud running near big data (e.g., interactive gateway to Spark)
* Enable a new breed of non-notebook web clients to provision and use kernels (e.g., web dashboards using [jupyter-js-services](https://github.com/jupyter/jupyter-js-services))
* Create microservices from notebooks using the Kernel Gateway [`notebook-http` mode](https://jupyter-kernel-gateway.readthedocs.io/en/latest/http-mode.html)

### Features

See the [Features page](https://jupyter-kernel-gateway.readthedocs.io/en/latest/features.html) in the 
documentation for a list of the Jupyter Kernel Gateway features.

## Installation

Detailed installation instructions are located in the
[Getting Started page](https://jupyter-kernel-gateway.readthedocs.io/en/latest/getting-started.html)
of the project docs. Here's a quick start using `pip`:

```bash
# install from pypi
pip install jupyter_kernel_gateway

# show all config options
jupyter kernelgateway --help-all

# run it with default options
jupyter kernelgateway
```

## Contributing

The [Development page](https://jupyter-kernel-gateway.readthedocs.io/en/latest/devinstall.html) includes information about setting up a development environment and typical developer tasks.
