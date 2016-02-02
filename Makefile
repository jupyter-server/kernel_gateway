# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

.PHONY: bash clean dev help install sdist test

IMAGE:=jupyter/pyspark-notebook:a388c4a66fd4

DOCKER_ARGS?=
define DOCKER
docker run -it --rm \
	--workdir '/srv/kernel_gateway' \
	-e PYTHONPATH='/srv/kernel_gateway' \
	-v `pwd`:/srv/kernel_gateway $(DOCKER_ARGS)
endef

help:
	@echo 'Host commands:'
	@echo '            bash - start an interactive shell within a container'
	@echo '           clean - clean built files'
	@echo '             dev - start kernel gateway server in a container'
	@echo '         install - install latest sdist into a container'
	@echo '           sdist - build a source distribution into dist/'
	@echo '            test - run unit tests within a container'
	@echo '    test-python2 - run unit tests explicitly using Python 2 within a container'
	@echo '    test-python3 - run unit tests explicitly using Python 3 within a container'

bash:
	@$(DOCKER) -p 8888:8888 $(IMAGE) bash

clean:
	@-rm -rf dist
	@-rm -rf *.egg-info
	@-find kernel_gateway -name __pycache__ -exec rm -fr {} \;
	@-find kernel_gateway -name '*.pyc' -exec rm -fr {} \;

dev: ARGS?=
dev: PYARGS?=
dev:
	@$(DOCKER) -p 8888:8888 $(IMAGE) \
		python $(PYARGS) kernel_gateway --KernelGatewayApp.ip='0.0.0.0' $(ARGS)

etc/api_examples/%:
	$(DOCKER) -p 8888:8888 $(IMAGE) \
		python $(PYARGS) kernel_gateway --KernelGatewayApp.ip='0.0.0.0' \
			--KernelGatewayApp.api='notebook-http' \
			--KernelGatewayApp.seed_uri=/srv/kernel_gateway/$@.ipynb $(ARGS)

install:
	$(DOCKER) $(IMAGE) bash -c "pip install dist/*.whl && \
		jupyter kernelgateway --help && \
		pip uninstall -y jupyter_kernel_gateway "
	$(DOCKER) $(IMAGE) bash -c "pip install dist/*.tar.gz && \
		jupyter kernelgateway --help && \
		pip uninstall -y jupyter_kernel_gateway"

bdist:
	$(DOCKER) $(IMAGE) python setup.py bdist_wheel $(POST_SDIST) \
	&& rm -rf *.egg-info

sdist:
	$(DOCKER) $(IMAGE) python setup.py sdist $(POST_SDIST) \
	&& rm -rf *.egg-info

test: test-python3

test-python2: PRE_CMD:=source activate python2; pip install requests;
test-python2: _test

test-python3: _test

_test: TEST?=
_test:
ifeq ($(TEST),)
	$(DOCKER) $(IMAGE) bash -c "$(PRE_CMD) nosetests"
else
# e.g., make test TEST="test_gatewayapp.TestGatewayAppConfig"
	@$(DOCKER) $(IMAGE) bash -c  "$(PRE_CMD) nosetests kernel_gateway.tests.$(TEST)"
endif

release: POST_SDIST=register upload
release: bdist sdist
