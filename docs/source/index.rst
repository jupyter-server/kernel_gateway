Jupyter Kernel Gateway
======================

Jupyter Kernel Gateway is a web server that provides headless access to
Jupyter kernels. Your application communicates with the kernels remotely,
through REST calls and Websockets rather than ZeroMQ messages.
There are no provisions for editing notebooks through the Kernel Gateway.
The following operation modes, called personalities, are supported
out of the box:

* Send code snippets for execution using the
  `Jupyter kernel protocol <https://jupyter-client.readthedocs.io/en/latest/messaging.html>`_
  over Websockets. Start and stop kernels through REST calls.
  This HTTP API is compatible with the respective API sections
  of the Jupyter Notebook server.

* Serve HTTP requests from annotated notebook cells. The code snippets
  are cells of a static notebook configured in the Kernel Gateway.
  Annotations define which HTTP verbs and resources it supports.
  Incoming requests are served by executing one of the cells in a kernel.

Jupyter Kernel Gateway uses the same code as Jupyter Notebook
to launch kernels in its local process/filesystem space.
It can be containerized and scaled out using common technologies like
`tmpnb <https://github.com/jupyter/tmpnb>`_,
`Cloud Foundry <https://github.com/cloudfoundry>`_, and
`Kubernetes <http://kubernetes.io/>`_.

.. image:: images/kg_basic.png
   :alt: Kernel Gateway basic deployment
   :width: 70%
   :align: center

.. toctree::
   :maxdepth: 2
   :caption: User Documentation

   getting-started
   uses
   features
   websocket-mode
   http-mode
   plug-in

.. toctree::
   :maxdepth: 2
   :caption: Configuration

   config-options
   troubleshooting

.. toctree::
   :maxdepth: 2
   :caption: Contributor Documentation

   devinstall

.. toctree::
   :maxdepth: 2
   :caption: Community Documentation

.. toctree::
   :maxdepth: 2
   :caption: About Jupyter Kernel Gateway

   summary-changes

.. toctree::
   :maxdepth: 2
   :caption: Questions? Suggestions?

   Jupyter mailing list <https://groups.google.com/forum/#!forum/jupyter>
   Jupyter website <https://jupyter.org>
   Stack Overflow - Jupyter <https://stackoverflow.com/questions/tagged/jupyter>
   Stack Overflow - Jupyter-notebook <https://stackoverflow.com/questions/tagged/jupyter-notebook>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
