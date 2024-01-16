# Getting started

This document describes some of the basics of installing and running the
Jupyter Kernel Gateway.

## Install

### Using pip

We make stable releases of the kernel gateway to PyPI. You can use `pip` to install the latest version along with its dependencies.

```bash
# install from pypi
pip install jupyter_kernel_gateway
```

### Using conda

You can install the kernel gateway using conda as well.

```bash
conda install -c conda-forge jupyter_kernel_gateway
```

## Running

Once installed, you can use the `jupyter` CLI to run the server.

```bash
# run it with default options
jupyter kernelgateway
```

For example, if we define an endpoint in a notebook `./my_example.ipynb` as follows:

```python
# GET /hello/world

import json
import requests
import numpy as np

req = json.loads(REQUEST)
res = dict(data=np.random.randn(5, 4).tolist(), request=req)
print(json.dumps(res))
```

and then run the gateway in [http-mode](http-mode.md) and point specifically at that notebook, we should see some information printed in the logs:

```bash
jupyter kernelgateway --KernelGatewayApp.api=kernel_gateway.notebook_http --KernelGatewayApp.seed_uri=./my_example.ipynb --port=10100
[KernelGatewayApp] Kernel started: 12ac2daa-c62a-47e4-964a-336734557656
[KernelGatewayApp] Registering resource: /hello/world, methods: (['GET'])
[KernelGatewayApp] Registering resource: /_api/spec/swagger.json, methods: (GET)
[KernelGatewayApp] Jupyter Kernel Gateway at http://127.0.0.1:10100
```

We can curl against these endpoints to demonstrate it is working:

```bash
curl http://127.0.0.1:10100/hello/world
{"data": [[0.25854873480479607, -0.7997878409880017, 1.1136688704814672, -1.3292395513862103], [1.9879386172897555, 0.43368279132553395, -0.8623363198491706, -0.1571285171759644], [0.4437134294167942, 1.1323758620715763, 1.7350545168735723, -0.7617257690860397], [-0.4219717996309759, 0.2912776236488964, -0.21468140988270742, -0.8286216351049279], [0.5754812112421828, -2.042429681534432, 2.992678912690803, -0.7231031350239057]], "request": {"body": "", "args": {}, "path": {}, "headers": {"Host": "127.0.0.1:10100", "User-Agent": "curl/7.68.0", "Accept": "*/*"}}}
```

and the swagger spec:

```bash
curl http://127.0.0.1:10100/_api/spec/swagger.json
{"swagger": "2.0", "paths": {"/hello/world": {"get": {"responses": {"200": {"description": "Success"}}}}}, "info": {"version": "0.0.0", "title": "my_example"}}
```

You can also run in the default [websocket-mode](websocket-mode.md):

```bash
jupyter kernelgateway --KernelGatewayApp.api=kernel_gateway.jupyter_websocket --port=10100
[KernelGatewayApp] Jupyter Kernel Gateway at http://127.0.0.1:10100
```

and again notice the output in the logs. This time we didn't point to a specific notebook but you can test against the kernelspecs endpoint or the swagger endpoint:

```bash
curl http://127.0.0.1:10100/api/kernelspecs
{"default": "python3", "kernelspecs": {"python38364bit38conda21f48c44b19044fba5c7aa244072a647": {"name": "python38364bit38conda21f48c44b19044fba5c7aa244072a647", ...
```

For more details running-mode sections [websocket-mode](websocket-mode.md) and [http-mode](http-mode.md).

**NOTE: Watch out for notebooks that run things on import as this might cause the gateway server to crash immediately and the log messages are not always obvious.**

## Running using a docker-stacks image

You can add the kernel gateway to any [docker-stacks](https://github.com/jupyter/docker-stacks) image by writing a Dockerfile patterned after the following example:

```bash
# start from the jupyter image with R, Python, and Scala (Apache Toree) kernels pre-installed
FROM jupyter/all-spark-notebook

# install the kernel gateway
RUN pip install jupyter_kernel_gateway

# run kernel gateway on container start, not notebook server
EXPOSE 8888
CMD ["jupyter", "kernelgateway", "--KernelGatewayApp.ip=0.0.0.0", "--KernelGatewayApp.port=8888"]
```

You can then build and run it.

```bash
docker build -t my/kernel-gateway .
docker run -it --rm -p 8888:8888 my/kernel-gateway
```
