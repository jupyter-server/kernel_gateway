# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Tests for jupyter-websocket mode."""

import json
import os
import uuid

import pytest
from jupyter_client.kernelspec import NoSuchKernel
from tornado.escape import json_decode, json_encode, url_escape
from tornado.gen import sleep
from tornado.httpclient import HTTPClientError
from tornado.web import HTTPError
from traitlets.config import Config

from kernel_gateway.gatewayapp import KernelGatewayApp
from kernel_gateway.services.kernels.manager import AsyncMappingKernelManager
from kernel_gateway.services.sessions.sessionmanager import SessionManager

from .test_gatewayapp import RESOURCES


@pytest.fixture()
def jp_server_config():
    """Allows tests to setup their specific configuration values."""
    config = {
        "KernelGatewayApp": {
            "api": "kernel_gateway.jupyter_websocket",
        }
    }
    return Config(config)


@pytest.fixture()
def spawn_kernel(jp_fetch, jp_http_port, jp_base_url, jp_ws_fetch):
    """Spawns a kernel where request.param contains the request body and returns the websocket."""

    async def _spawn_kernel(body="{}"):
        # Request a kernel
        response = await jp_fetch("api", "kernels", method="POST", body=body)
        assert response.code == 201

        # Connect to the kernel via websocket
        kernel = json_decode(response.body)
        kernel_id = kernel["id"]
        ws = await jp_ws_fetch("api", "kernels", kernel_id, "channels")
        return ws

    return _spawn_kernel


def get_execute_request(code: str) -> dict:
    """Creates an execute_request message.

    Parameters
    ----------
    code : str
        Code to execute

    Returns
    -------
    dict
        The message
    """
    return {
        "header": {
            "username": "",
            "version": "5.0",
            "session": "",
            "msg_id": "fake-msg-id",
            "msg_type": "execute_request",
        },
        "parent_header": {},
        "channel": "shell",
        "content": {"code": code, "silent": False, "store_history": False, "user_expressions": {}},
        "metadata": {},
        "buffers": {},
    }


async def await_stream(ws):
    """Returns stream output associated with an execute_request."""
    while 1:
        msg = await ws.read_message()
        msg = json_decode(msg)
        msg_type = msg["msg_type"]
        parent_msg_id = msg["parent_header"]["msg_id"]
        if msg_type == "stream" and parent_msg_id == "fake-msg-id":
            return msg["content"]


class TestDefaults:
    """Tests gateway behavior."""

    @pytest.mark.parametrize("jp_argv", (["--JupyterWebsocketPersonality.list_kernels=True"],))
    async def test_startup(self, jp_fetch, jp_argv):
        """Root of kernels resource should be OK."""
        response = await jp_fetch("api", "kernels", method="GET")
        assert response.code == 200

    async def test_headless(self, jp_fetch):
        """Other notebook resources should not exist."""
        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("api", "contents", method="GET")
        assert e.value.code == 404

        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("", method="GET")
        assert e.value.code == 404

        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("tree", method="GET")
        assert e.value.code == 404

    async def test_check_origin(self, jp_fetch, jp_web_app):
        """Allow origin setting should pass through to base handlers."""
        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("api", "kernelspecs", headers={"Origin": "fake.com:8888"}, method="GET")
        assert e.value.code == 404

        jp_web_app.settings["allow_origin"] = "*"

        response = await jp_fetch(
            "api", "kernelspecs", headers={"Origin": "fake.com:8888"}, method="GET"
        )
        assert response.code == 200

    @pytest.mark.parametrize(
        "jp_server_config",
        (
            Config(
                {
                    "KernelGatewayApp": {
                        "api": "notebook-gopher",
                    }
                }
            ),
        ),
    )
    async def test_config_bad_api_value(self, jp_configurable_serverapp, jp_server_config):
        """Should raise an ImportError for nonexistent API personality modules."""
        with pytest.raises(ImportError):
            await jp_configurable_serverapp()

    async def test_options_without_auth_token(self, jp_fetch, jp_web_app):
        """OPTIONS requests doesn't need to submit a token. Used for CORS preflight."""
        # Confirm that OPTIONS request doesn't require token
        response = await jp_fetch("api", method="OPTIONS")
        assert response.code == 200

    @pytest.mark.parametrize(
        "jp_server_config",
        (
            Config(
                {
                    "KernelGatewayApp": {
                        "auth_token": "fake-token",
                    }
                }
            ),
        ),
    )
    async def test_auth_token(self, jp_server_config, jp_fetch, jp_web_app, jp_ws_fetch):
        """All server endpoints should check the configured auth token."""

        # Request API without the token
        # Note that we'd prefer not to set _any_ header, but `fp_auth_header` will force it
        # to be set, so setting the empty authorization header is necessary for the tests
        # asserting 401.
        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("api", method="GET", headers={"Authorization": ""})
        assert e.value.response.code == 401

        # Now with it
        response = await jp_fetch(
            "api", method="GET", headers={"Authorization": "token fake-token"}
        )
        assert response.code == 200

        # Request kernelspecs without the token
        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("api", "kernelspecs", method="GET", headers={"Authorization": ""})
        assert e.value.response.code == 401

        # Now with it
        response = await jp_fetch(
            "api", "kernelspecs", method="GET", headers={"Authorization": "token fake-token"}
        )
        assert response.code == 200

        # Request a kernel without the token
        with pytest.raises(HTTPClientError) as e:
            await jp_fetch(
                "api", "kernels", method="POST", body="{}", headers={"Authorization": ""}
            )
        assert e.value.response.code == 401

        # Now with it
        response = await jp_fetch(
            "api",
            "kernels",
            method="POST",
            body="{}",
            headers={"Authorization": "token fake-token"},
        )
        assert response.code == 201
        kernel = json_decode(response.body)
        kernel_id = url_escape(kernel["id"])

        # Request kernel info without the token
        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("api", "kernels", kernel_id, method="GET", headers={"Authorization": ""})
        assert e.value.response.code == 401

        # Now with it
        response = await jp_fetch(
            "api", "kernels", kernel_id, method="GET", headers={"Authorization": "token fake-token"}
        )
        assert response.code == 200

        # Request websocket connection without the token

        # No option to ignore errors so try/except
        with pytest.raises(HTTPClientError) as e:
            await jp_ws_fetch(
                "api", "kernels", kernel_id, "channels", headers={"Authorization": ""}
            )
        assert e.value.response.code == 401

        # Now request the websocket with the token
        ws = await jp_ws_fetch(
            "api", "kernels", kernel_id, "channels", headers={"Authorization": "token fake-token"}
        )
        ws.close()

    async def test_cors_headers(self, jp_fetch, jp_web_app):
        """All kernel endpoints should respond with configured CORS headers."""

        jp_web_app.settings["kg_allow_credentials"] = "false"
        jp_web_app.settings["kg_allow_headers"] = "Authorization,Content-Type"
        jp_web_app.settings["kg_allow_methods"] = "GET,POST"
        jp_web_app.settings["kg_allow_origin"] = "https://jupyter.org"
        jp_web_app.settings["kg_expose_headers"] = "X-My-Fake-Header"
        jp_web_app.settings["kg_max_age"] = "600"
        jp_web_app.settings["kg_list_kernels"] = True

        # Get kernels to check headers
        response = await jp_fetch("api", "kernels", method="GET")
        assert response.code == 200
        assert response.headers["Access-Control-Allow-Credentials"] == "false"
        assert response.headers["Access-Control-Allow-Headers"] == "Authorization,Content-Type"
        assert response.headers["Access-Control-Allow-Methods"] == "GET,POST"
        assert response.headers["Access-Control-Allow-Origin"] == "https://jupyter.org"
        assert response.headers["Access-Control-Expose-Headers"] == "X-My-Fake-Header"
        assert response.headers["Access-Control-Max-Age"] == "600"
        assert response.headers.get("Content-Security-Policy") is None

    async def test_cors_options_headers(self, jp_fetch, jp_web_app):
        """All preflight OPTIONS requests should return configured headers."""
        jp_web_app.settings["kg_allow_headers"] = "X-XSRFToken"
        jp_web_app.settings["kg_allow_methods"] = "GET,POST,OPTIONS"

        response = await jp_fetch("api", "kernelspecs", method="OPTIONS")
        assert response.code == 200
        assert response.headers["Access-Control-Allow-Methods"] == "GET,POST,OPTIONS"
        assert response.headers["Access-Control-Allow-Headers"] == "X-XSRFToken"

    async def test_max_kernels(self, jp_fetch, jp_web_app):
        """Number of kernels should be limited."""
        jp_web_app.settings["kg_max_kernels"] = 1

        # Request a kernel
        response = await jp_fetch("api", "kernels", method="POST", body="{}")
        assert response.code == 201

        # Request another
        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("api", "kernels", method="POST", body="{}")
        assert e.value.response.code == 403

        # Shut down the kernel
        kernel = json_decode(response.body)
        response = await jp_fetch("api", "kernels", url_escape(kernel["id"]), method="DELETE")
        assert response.code == 204

        # Try creation again
        response = await jp_fetch("api", "kernels", method="POST", body="{}")
        assert response.code == 201

    async def test_get_api(self, jp_fetch):
        """Server should respond with the API version metadata."""
        response = await jp_fetch("api", method="GET")
        assert response.code == 200
        info = json_decode(response.body)
        assert "version" in info

    async def test_get_kernelspecs(self, jp_fetch):
        """Server should respond with kernel spec metadata."""
        response = await jp_fetch("api", "kernelspecs", method="GET")
        assert response.code == 200
        specs = json_decode(response.body)
        assert "kernelspecs" in specs
        assert "default" in specs

    async def test_get_kernels(self, jp_fetch, jp_web_app):
        """Server should respond with running kernel information."""
        jp_web_app.settings["kg_list_kernels"] = True
        response = await jp_fetch("api", "kernels", method="GET")
        assert response.code == 200
        kernels = json_decode(response.body)
        assert len(kernels) == 0

        # Launch a kernel
        response = await jp_fetch("api", "kernels", method="POST", body="{}")
        assert response.code == 201
        kernel = json_decode(response.body)

        # Check the list again
        response = await jp_fetch("api", "kernels", method="GET")
        assert response.code == 200
        kernels = json_decode(response.body)
        assert len(kernels) == 1
        assert kernels[0]["id"] == kernel["id"]

    async def test_kernel_comm(self, spawn_kernel):
        """Default kernel should launch and accept commands."""
        ws = await spawn_kernel()

        # Send a request for kernel info
        await ws.write_message(
            json_encode(
                {
                    "header": {
                        "username": "",
                        "version": "5.0",
                        "session": "",
                        "msg_id": "fake-msg-id",
                        "msg_type": "kernel_info_request",
                    },
                    "parent_header": {},
                    "channel": "shell",
                    "content": {},
                    "metadata": {},
                    "buffers": {},
                }
            )
        )

        # Assert the reply comes back. Test will timeout if this hangs.
        for _ in range(10):
            msg = await ws.read_message()
            msg = json_decode(msg)
            if msg["msg_type"] == "kernel_info_reply":
                break
        else:
            raise AssertionError("never received kernel_info_reply")
        ws.close()

    async def test_no_discovery(self, jp_fetch):
        """The list of kernels / sessions should be forbidden by default."""
        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("api", "kernels", method="GET")
        assert e.value.response.code == 403

        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("api", "sessions", method="GET")
        assert e.value.response.code == 403

    async def test_crud_sessions(self, jp_fetch, jp_web_app):
        """Server should create, list, and delete sessions."""
        jp_web_app.settings["kg_list_kernels"] = True

        # Ensure no sessions by default
        response = await jp_fetch("api", "sessions", method="GET")
        assert response.code == 200
        sessions = json_decode(response.body)
        assert len(sessions) == 0

        # Launch a session
        response = await jp_fetch(
            "api",
            "sessions",
            method="POST",
            body='{"id":"any","notebook":{"path":"anywhere"},"kernel":{"name":"python"}}',
        )
        assert response.code == 201
        session = json_decode(response.body)

        # Check the list again
        response = await jp_fetch("api", "sessions", method="GET")
        assert response.code == 200
        sessions = json_decode(response.body)
        assert len(sessions) == 1
        assert sessions[0]["id"] == session["id"]

        # Delete the session
        response = await jp_fetch("api", "sessions", session["id"], method="DELETE")
        assert response.code == 204

        # Make sure the list is empty
        response = await jp_fetch("api", "sessions", method="GET")
        assert response.code == 200
        sessions = json_decode(response.body)
        assert len(sessions) == 0

    async def test_json_errors(self, jp_fetch):
        """Handlers should always return JSON errors."""
        # A handler that we override
        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("api", "kernels", method="GET")
        assert e.value.response.code == 403

        body = json_decode(e.value.response.body)
        assert body["reason"] == "Forbidden"

        # A handler from the notebook base
        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("api", "kernels", "1-2-3-4-5", method="GET")
        assert e.value.response.code == 404

        body = json_decode(e.value.response.body)
        assert "1-2-3-4-5" in body["message"]

        # The last resort not found handler
        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("fake-endpoint", method="GET")
        assert e.value.response.code == 404

        body = json_decode(e.value.response.body)
        assert body["reason"] == "Not Found"

    @pytest.mark.parametrize("jp_argv", (["--JupyterWebsocketPersonality.env_whitelist=TEST_VAR"],))
    async def test_kernel_env(self, spawn_kernel, jp_argv):
        """Kernel should start with environment vars defined in the request."""

        kernel_body = json.dumps(
            {
                "name": "python",
                "env": {
                    "KERNEL_FOO": "kernel-foo-value",
                    "NOT_KERNEL": "ignored",
                    "KERNEL_GATEWAY": "overridden",
                    "TEST_VAR": "allowed",
                },
            }
        )
        ws = await spawn_kernel(kernel_body)
        req = get_execute_request(
            'import os; print(os.getenv("KERNEL_FOO"), os.getenv("NOT_KERNEL"), '
            'os.getenv("KERNEL_GATEWAY"), os.getenv("TEST_VAR"))'
        )

        await ws.write_message(json_encode(req))
        content = await await_stream(ws)

        assert content["name"] == "stdout"
        assert "kernel-foo-value" in content["text"]
        assert "ignored" not in content["text"]
        assert "overridden" not in content["text"]
        assert "allowed" in content["text"]
        ws.close()

    async def test_get_swagger_yaml_spec(self, jp_fetch):
        """Getting the swagger.yaml spec should be ok"""
        response = await jp_fetch("api", "swagger.yaml", method="GET")
        assert response.code == 200

    async def test_get_swagger_json_spec(self, jp_fetch):
        """Getting the swagger.json spec should be ok"""
        response = await jp_fetch("api", "swagger.json", method="GET")
        assert response.code == 200

    async def test_kernel_env_auth_token(self, monkeypatch, spawn_kernel):
        """Kernel should not have KG_AUTH_TOKEN in its environment."""
        monkeypatch.setenv("KG_AUTH_TOKEN", "fake-secret")

        ws = None
        try:
            ws = await spawn_kernel()
            req = get_execute_request("import os; print(os.getenv('KG_AUTH_TOKEN'))")
            await ws.write_message(json_encode(req))
            content = await await_stream(ws)
            assert "fake-secret" not in content["text"]
            assert "None" in content["text"]  # ensure None was printed
        finally:
            if ws is not None:
                ws.close()


@pytest.mark.parametrize("jp_argv", (["--KernelGatewayApp.default_kernel_name=fake-kernel"],))
class TestCustomDefaultKernel:
    """Tests gateway behavior when setting a custom default kernelspec."""

    async def test_default_kernel_name(self, jp_argv, jp_fetch):
        """The default kernel name should be used on empty requests."""
        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("api", "kernels", method="POST", body="")
        assert e.value.response.code == 500
        assert "raise NoSuchKernel" in str(e.value.response.body)


@pytest.mark.parametrize(
    "jp_argv",
    (
        [
            "--KernelGatewayApp.prespawn_count=2",
            f"--KernelGatewayApp.seed_uri={os.path.join(RESOURCES, 'zen.ipynb')}",
            "--KernelGatewayApp.force_kernel_name=python3",
        ],
    ),
)
class TestForceKernel:
    """Tests gateway behavior when forcing a kernelspec."""

    async def test_force_kernel_name(self, jp_argv, jp_fetch):
        """Should create a Python kernel."""
        response = await jp_fetch("api", "kernels", method="POST", body='{"name": "fake-kernel"}')
        assert response.code == 201
        kernel = json_decode(response.body)
        assert kernel["name"] == "python3"


class TestEnableDiscovery:
    """Tests gateway behavior with kernel listing enabled."""

    @pytest.mark.parametrize("jp_argv", (["--JupyterWebsocketPersonality.list_kernels=True"],))
    async def test_enable_kernel_list(self, jp_fetch, jp_argv):
        """The list of kernels, sessions, and activities should be available."""

        response = await jp_fetch("api", "kernels", method="GET")
        assert response.code == 200
        assert "[]" in str(response.body)

        response = await jp_fetch("api", "sessions", method="GET")
        assert response.code == 200
        assert "[]" in str(response.body)


class TestPrespawnKernels:
    """Tests gateway behavior when kernels are spawned at startup."""

    @pytest.mark.parametrize("jp_argv", (["--KernelGatewayApp.prespawn_count=2"],))
    async def test_prespawn_count(self, jp_fetch, jp_web_app, jp_argv):
        """Server should launch the given number of kernels on startup."""
        jp_web_app.settings["kg_list_kernels"] = True
        await sleep(0.5)
        response = await jp_fetch("api", "kernels", method="GET")
        assert response.code == 200

        kernels = json_decode(response.body)
        assert len(kernels) == 2

    def test_prespawn_max_conflict(self):
        """Server should error if prespawn count is greater than max allowed kernels."""
        app = KernelGatewayApp()
        app.prespawn_count = 3
        app.max_kernels = 2
        with pytest.raises(RuntimeError):
            app.init_configurables()


class TestBaseURL:
    """Tests gateway behavior when a custom base URL is configured."""

    @pytest.mark.parametrize("jp_argv", (["--JupyterWebsocketPersonality.list_kernels=True"],))
    @pytest.mark.parametrize("jp_base_url", ("/fake/path",))
    async def test_base_url(self, jp_base_url, jp_argv, jp_fetch):
        """Server should mount resources under configured base."""
        # Should exist under path
        response = await jp_fetch("api", "kernels", method="GET")
        assert response.code == 200
        assert "/fake/path/api/kernels" in response.effective_url


class TestRelativeBaseURL:
    """Tests gateway behavior when a relative base URL is configured."""

    @pytest.mark.parametrize("jp_argv", (["--JupyterWebsocketPersonality.list_kernels=True"],))
    @pytest.mark.parametrize("jp_base_url", ("/fake/path",))
    async def test_base_url(self, jp_base_url, jp_argv, jp_fetch):
        """Server should mount resources under fixed base."""

        # Should exist under path
        response = await jp_fetch("api", "kernels", method="GET")
        assert response.code == 200
        assert "/fake/path/api/kernels" in response.effective_url


class TestSeedURI:
    """Tests gateway behavior when a seeding kernel memory with code from a notebook."""

    @pytest.mark.parametrize(
        "jp_argv", ([f"--KernelGatewayApp.seed_uri={os.path.join(RESOURCES, 'zen.ipynb')}"],)
    )
    async def test_seed(self, jp_argv, spawn_kernel):
        """Kernel should have variables pre-seeded from the notebook."""
        ws = await spawn_kernel()

        # Print the encoded "zen of python" string, the kernel should have
        # it imported
        req = get_execute_request("print(this.s)")
        await ws.write_message(json_encode(req))
        content = await await_stream(ws)
        assert content["name"] == "stdout"
        assert "Gur Mra bs Clguba" in content["text"]

        ws.close()


class TestRemoteSeedURI:
    """Tests gateway behavior when a seeding kernel memory with code from a remote notebook."""

    @pytest.mark.parametrize(
        "jp_argv",
        (
            [
                "--KernelGatewayApp.seed_uri="
                "https://gist.githubusercontent.com/parente/ccd36bd7db2f617d58ce/raw/zen3.ipynb"
            ],
        ),
    )
    async def test_seed(self, jp_argv, spawn_kernel):
        """Kernel should have variables pre-seeded from the notebook."""
        ws = await spawn_kernel()

        # Print the encoded "zen of python" string, the kernel should have
        # it imported
        req = get_execute_request("print(this.s)")
        await ws.write_message(json_encode(req))
        content = await await_stream(ws)
        assert content["name"] == "stdout"
        assert "Gur Mra bs Clguba" in content["text"]

        ws.close()


class TestBadSeedURI:
    """Tests gateway behavior when seeding kernel memory with notebook code that fails."""

    @pytest.mark.parametrize(
        "jp_argv",
        (
            [
                f"--KernelGatewayApp.seed_uri={os.path.join(RESOURCES, 'failing_code.ipynb')}",
                "--JupyterWebsocketPersonality.list_kernels=True",
            ],
        ),
    )
    async def test_seed_error(self, jp_argv, jp_fetch):
        """
        Server should shutdown kernel and respond with error when seed notebook
        has an execution error.
        """

        # Request a kernel
        with pytest.raises(HTTPClientError) as e:
            await jp_fetch("api", "kernels", method="POST", body="{}")
        assert e.value.response.code == 500

        # No kernels should be running
        response = await jp_fetch("api", "kernels", method="GET")
        assert response.code == 200
        kernels = json_decode(response.body)
        assert len(kernels) == 0

    async def test_seed_kernel_not_available(self):
        """
        Server should error because seed notebook requires a kernel that is not installed.
        """
        app = KernelGatewayApp()
        app.seed_uri = os.path.join(RESOURCES, "unknown_kernel.ipynb")
        with pytest.raises(NoSuchKernel):
            app.init_configurables()


@pytest.mark.parametrize(
    "jp_argv",
    (
        [
            f"--KernelGatewayApp.seed_uri={os.path.join(RESOURCES, 'zen.ipynb')}",
            "--KernelGatewayApp.prespawn_count=1",
        ],
    ),
)
class TestKernelLanguageSupport:
    """Tests gateway behavior when a client requests a specific kernel spec."""

    async def test_seed_language_support(self, jp_argv, spawn_kernel):
        """Kernel should have variables pre-seeded from notebook."""
        ws = await spawn_kernel(body=json.dumps({"name": "python3"}))
        code = "print(this.s)"

        # Print the encoded "zen of python" string, the kernel should have it imported
        req = get_execute_request(code)
        await ws.write_message(json_encode(req))
        content = await await_stream(ws)
        assert content["name"] == "stdout"
        assert "Gur Mra bs Clguba" in content["text"]

        ws.close()


class TestSessionApi:
    """Test session object API to improve coverage."""

    async def test_session_api(self, tmp_path, jp_environ):
        # Create the manager instances
        akm = AsyncMappingKernelManager()
        sm = SessionManager(akm)

        row_model = await sm.create_session(path=str(tmp_path), kernel_name="python3")
        assert "id" in row_model
        assert "kernel" in row_model
        assert row_model["notebook"]["path"] == str(tmp_path)

        session_id = row_model["id"]
        kernel_id = row_model["kernel"]["id"]

        # Perform some get_session tests
        with pytest.raises(TypeError):
            sm.get_session()  # no kwargs

        with pytest.raises(TypeError):
            kwargs = {"bogus_column": 1}
            sm.get_session(**kwargs)  # bad column

        non_existent_session_id = uuid.uuid4()
        with pytest.raises(HTTPError) as e:
            kwargs = {"session_id": str(non_existent_session_id)}
            sm.get_session(**kwargs)  # bad session id
        assert e.value.status_code == 404

        # Perform some update_session tests
        sm.update_session(session_id)  # no kwargs - success expected

        with pytest.raises(KeyError):
            kwargs = {"kernel_id": kernel_id}
            sm.update_session(str(non_existent_session_id), **kwargs)  # bad session id

        kwargs = {"path": "/tmp"}
        sm.update_session(session_id, **kwargs)  # update path of session

        # confirm update
        kwargs = {"session_id": session_id}
        row_model = sm.get_session(**kwargs)
        assert row_model["notebook"]["path"] == "/tmp"

        kwargs = {"kernel_id": str(uuid.uuid4())}
        with pytest.raises(KeyError):
            sm.update_session(session_id, **kwargs)  # bad kernel_id

        await sm.delete_session(session_id)

        with pytest.raises(HTTPError) as e:
            kwargs = {"session_id": session_id}
            sm.get_session(**kwargs)
        assert e.value.status_code == 404
