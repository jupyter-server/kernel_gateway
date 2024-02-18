# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Tests for notebook-http mode."""

import asyncio
import json
import os

import pytest
from tornado.httpclient import HTTPClientError
from traitlets.config import Config

from kernel_gateway.notebook_http.swagger.handlers import SwaggerSpecHandler

from .test_gatewayapp import RESOURCES


@pytest.fixture()
def jp_server_config():
    """Allows tests to setup their specific configuration values."""
    config = {
        "KernelGatewayApp": {
            "api": "kernel_gateway.notebook_http",
            "seed_uri": os.path.join(RESOURCES, "kernel_api.ipynb"),
        }
    }
    return Config(config)


class TestDefaults:
    """Tests gateway behavior."""

    async def test_api_get_endpoint(self, jp_fetch):
        """GET HTTP method should be callable"""
        response = await jp_fetch("hello", method="GET")
        assert response.code == 200, "GET endpoint did not return 200."
        assert response.body == b"hello world\n", "Unexpected body in response to GET."

    async def test_api_get_endpoint_with_path_param(self, jp_fetch):
        """GET HTTP method should be callable with a path param"""
        response = await jp_fetch("hello", "governor", method="GET")
        assert response.code == 200, "GET endpoint did not return 200."
        assert response.body == b"hello governor\n", "Unexpected body in response to GET."

    async def test_api_get_endpoint_with_query_param(self, jp_fetch):
        """GET HTTP method should be callable with a query param"""
        response = await jp_fetch("hello", "person", params={"person": "governor"}, method="GET")
        assert response.code == 200, "GET endpoint did not return 200."
        print(f"response.body = '{response.body}'")
        assert response.body == b"hello governor\n", "Unexpected body in response to GET."

    async def test_api_get_endpoint_with_multiple_query_params(self, jp_fetch):
        """GET HTTP method should be callable with multiple query params"""
        response = await jp_fetch(
            "hello", "persons", params={"person": "governor, rick"}, method="GET"
        )
        assert response.code == 200, "GET endpoint did not return 200."
        assert response.body == b"hello governor, rick\n", "Unexpected body in response to GET."

    async def test_api_put_endpoint(self, jp_fetch):
        """PUT HTTP method should be callable"""
        response = await jp_fetch("message", method="PUT", body="hola {}")
        assert response.code == 200, "PUT endpoint did not return 200."

        response = await jp_fetch("message", method="GET")
        assert response.code == 200, "GET endpoint did not return 200."
        assert (
            response.body == b"hola {}\n"
        ), "Unexpected body in response to GET after performing PUT."

    async def test_api_post_endpoint(self, jp_fetch):
        """POST endpoint should be callable"""
        expected = b'["Rick", "Maggie", "Glenn", "Carol", "Daryl"]\n'
        response = await jp_fetch(
            "people",
            method="POST",
            body=expected.decode("UTF-8"),
            headers={"Content-Type": "application/json"},
        )
        assert response.code == 200, "POST endpoint did not return 200."
        assert response.body == expected, "Unexpected body in response to POST."

    async def test_api_delete_endpoint(self, jp_fetch):
        """DELETE HTTP method should be callable"""
        expected = b'["Rick", "Maggie", "Glenn", "Carol", "Daryl"]\n'
        response = await jp_fetch(
            "people",
            method="POST",
            body=expected.decode("UTF-8"),
            headers={"Content-Type": "application/json"},
        )
        response = await jp_fetch("people", "2", method="DELETE")
        assert response.code == 200, "DELETE endpoint did not return 200."
        assert (
            response.body == b'["Rick", "Maggie", "Carol", "Daryl"]\n'
        ), "Unexpected body in response to DELETE."

    async def test_api_error_endpoint(self, jp_fetch):
        """Error in a cell should cause 500 HTTP status"""
        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("error", method="GET")
        assert e.value.code == 500, "Cell with error did not return 500 status code."

    async def test_api_stderr_endpoint(self, jp_fetch):
        """stderr output in a cell should be dropped"""
        response = await jp_fetch("stderr", method="GET")
        assert response.body == b"I am text on stdout\n", "Unexpected text in response"

    async def test_api_unsupported_method(self, jp_fetch):
        """Endpoints which do no support an HTTP verb should respond with 405."""
        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("message", method="DELETE")
        assert (
            e.value.code == 405
        ), "Endpoint which exists, but does not support DELETE, did not return 405 status code."

    async def test_api_undefined(self, jp_fetch):
        """Endpoints which are not registered at all should respond with 404."""
        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("not", "an", "endpoint", method="GET")

        assert (
            e.value.code == 404
        ), "Endpoint which should not exist did not return 404 status code."
        body = json.loads(e.value.response.body.decode("UTF-8"))
        assert body["reason"] == "Not Found"

    async def test_api_access_http_header(self, jp_fetch):
        """HTTP endpoints should be able to access request headers"""
        content_types = ["text/plain", "application/json", "application/atom+xml", "foo"]
        for content_type in content_types:
            response = await jp_fetch(
                "content-type", method="GET", headers={"Content-Type": content_type}
            )
            assert response.code == 200, "GET endpoint did not return 200."
            assert (
                response.body.decode(encoding="UTF-8") == f"{content_type}\n"
            ), "Unexpected value in response"

    async def test_format_request_code_escaped_integration(self, jp_fetch):
        """Quotes should be properly escaped in request headers."""
        # Test query with escaping of arguments and headers with multiple escaped quotes
        response = await jp_fetch(
            "hello",
            "person",
            params={"person": "governor"},
            method="GET",
            headers={"If-None-Match": '""9a28a9262f954494a8de7442c63d6d0715ce0998""'},
        )
        assert response.code == 200, "GET endpoint did not return 200."
        assert response.body == b"hello governor\n", "Unexpected body in response to GET."

    async def test_blocked_download_notebook_source(self, jp_fetch):
        """Notebook source should not exist under the path /_api/source when
        `allow_notebook_download` is False or not configured.
        """
        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("_api", "source", method="GET")
        assert e.value.code == 404, "/_api/source found when allow_notebook_download is false"

    async def test_blocked_public(self, jp_fetch):
        """Public static assets should not exist under the path /public when
        `static_path` is False or not configured.
        """
        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("public", method="GET")
        assert e.value.code == 404, "/public found when static_path is false"

    async def test_api_returns_execute_result(self, jp_fetch):
        """GET HTTP method should return the result of cell execution"""
        response = await jp_fetch("execute_result", method="GET")
        assert response.code == 200, "GET endpoint did not return 200."
        assert response.body == b'{"text/plain": "2"}', "Unexpected body in response to GET."

    async def test_cells_concatenate(self, jp_fetch):
        """Multiple cells with the same verb and path should concatenate."""
        response = await jp_fetch("multi", method="GET")
        assert response.code == 200, "GET endpoint did not return 200."
        assert response.body == b"x is 1\n", "Unexpected body in response to GET."

    async def test_kernel_gateway_environment_set(self, jp_fetch):
        """GET HTTP method should be callable with multiple query params"""
        response = await jp_fetch("env_kernel_gateway", method="GET")
        assert response.code == 200, "GET endpoint did not return 200."
        assert response.body == b"KERNEL_GATEWAY is 1\n", "Unexpected body in response to GET."


@pytest.mark.parametrize(
    "jp_argv", ([f"--NotebookHTTPPersonality.static_path={os.path.join(RESOURCES, 'public')}"],)
)
class TestPublicStatic:
    """Tests gateway behavior when public static assets are enabled."""

    async def test_get_public(self, jp_fetch, jp_argv):
        """index.html should exist under `/public/index.html`."""
        response = await jp_fetch("public", "index.html", method="GET")
        assert response.code == 200
        assert response.headers.get("Content-Type") == "text/html"


@pytest.mark.parametrize("jp_argv", (["--NotebookHTTPPersonality.allow_notebook_download=True"],))
class TestSourceDownload:
    """Tests gateway behavior when notebook download is allowed."""

    async def test_download_notebook_source(self, jp_fetch, jp_argv):
        """Notebook source should exist under the path `/_api/source`."""
        response = await jp_fetch("_api", "source", method="GET")
        assert response.code == 200, "/_api/source did not correctly return the downloaded notebook"
        nb = json.loads(response.body)
        for key in ["cells", "metadata", "nbformat", "nbformat_minor"]:
            assert key in nb


@pytest.mark.parametrize(
    "jp_argv", ([f"--KernelGatewayApp.seed_uri={os.path.join(RESOURCES, 'responses.ipynb')}"],)
)
class TestCustomResponse:
    """Tests gateway behavior when the notebook contains ResponseInfo cells."""

    async def test_setting_content_type(self, jp_fetch, jp_argv):
        """A response cell should allow the content type to be set"""
        response = await jp_fetch("json", method="GET")
        result = json.loads(response.body.decode("UTF-8"))
        assert response.code == 200, "Response status was not 200"
        assert (
            response.headers["Content-Type"] == "application/json"
        ), "Incorrect mime type was set on response"
        assert result == {"hello": "world"}, "Incorrect response value."

    async def test_setting_response_status_code(self, jp_fetch, jp_argv):
        """A response cell should allow the response status code to be set"""
        response = await jp_fetch("nocontent", method="GET")
        assert response.code == 204, "Response status was not 204"
        assert response.body == b"", "Incorrect response value."

    async def test_setting_etag_header(self, jp_fetch, jp_argv):
        """A response cell should allow the etag header to be set"""
        response = await jp_fetch("etag", method="GET")
        result = json.loads(response.body.decode("UTF-8"))
        assert response.code == 200, "Response status was not 200"
        assert (
            response.headers["Content-Type"] == "application/json"
        ), "Incorrect mime type was set on response"
        assert result, {"hello": "world"} == "Incorrect response value."
        assert response.headers["Etag"] == "1234567890", "Incorrect Etag header value."


@pytest.mark.parametrize("jp_argv", (["--KernelGatewayApp.prespawn_count=3"],))
class TestKernelPool:
    async def test_should_cycle_through_kernels(self, jp_fetch, jp_argv):
        """Requests should cycle through kernels"""
        response = await jp_fetch("message", method="PUT", body="hola {}")
        assert response.code == 200, "PUT endpoint did not return 200."

        for i in range(3):
            response = await jp_fetch("message", method="GET")

            if i != 2:
                assert (
                    response.body == b"hello {}\n"
                ), "Unexpected body in response to GET after performing PUT."
            else:
                assert (
                    response.body == b"hola {}\n"
                ), "Unexpected body in response to GET after performing PUT."

    @pytest.mark.timeout(20)
    async def test_concurrent_request_should_not_be_blocked(self, jp_fetch, jp_argv):
        """Concurrent requests should not be blocked"""
        response_long_running = jp_fetch("sleep", "6", method="GET")
        assert response_long_running.done() is False, "Long HTTP Request is not running"

        response_short_running = await jp_fetch("sleep", "3", method="GET")
        assert (
            response_short_running.code == 200
        ), "Short HTTP Request did not return proper status code of 200"
        assert response_long_running.done() is False, "Long HTTP Request is not running"
        while not response_long_running.done():
            await asyncio.sleep(0.3)  # let the long request complete

    async def test_locking_semaphore_of_kernel_resources(self, jp_fetch, jp_argv):
        """Kernel pool should prevent more than one request from running on a kernel at a time."""
        futures = []
        for _ in range(7):
            futures.append(jp_fetch("sleep", "1", method="GET"))

        count = 0
        for future in futures:
            await future
            count += 1
            if count >= 4:
                break

        for future in futures:
            await future


@pytest.mark.parametrize(
    "jp_argv", ([f"--KernelGatewayApp.seed_uri={os.path.join(RESOURCES, 'simple_api.ipynb')}"],)
)
class TestSwaggerSpec:
    async def test_generation_of_swagger_spec(self, jp_fetch, jp_argv):
        """Server should expose a swagger specification of its notebook-defined
        API.
        """
        expected_response = {
            "info": {"version": "0.0.0", "title": "simple_api"},
            "paths": {
                "/name": {
                    "get": {"responses": {"200": {"description": "Success"}}},
                    "post": {"responses": {"200": {"description": "Success"}}},
                }
            },
            "swagger": "2.0",
        }

        response = await jp_fetch("_api", "spec", "swagger.json", method="GET")
        result = json.loads(response.body.decode("UTF-8"))
        assert response.code == 200, "Swagger spec endpoint did not return the correct status code"
        assert result == expected_response, "Swagger spec endpoint did not return the correct value"
        assert (
            SwaggerSpecHandler.output is not None
        ), "Swagger spec output wasn't cached for later requests"


@pytest.mark.parametrize(
    "jp_argv",
    (
        [
            f"--KernelGatewayApp.seed_uri={os.path.join(RESOURCES, 'unknown_kernel.ipynb')}",
            "--KernelGatewayApp.force_kernel_name=python3",
        ],
    ),
)
class TestForceKernel:
    async def test_force_kernel_spec(self, jp_fetch, jp_argv):
        """Should start properly.."""
        response = await jp_fetch("_api", "spec", "swagger.json", method="GET")
        assert response.code == 200
