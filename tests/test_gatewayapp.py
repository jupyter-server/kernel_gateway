# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Tests for basic gateway app behavior."""
import os
import ssl

import nbformat

from kernel_gateway import __version__
from kernel_gateway.gatewayapp import KernelGatewayApp

RESOURCES = os.path.join(os.path.dirname(__file__), "resources")


class TestGatewayAppConfig:
    """Tests configuration of the gateway app."""

    def test_config_env_vars(self, monkeypatch):
        """Env vars should be honored for traitlets."""
        # Environment vars are always strings
        monkeypatch.setenv("KG_PORT", "1234")
        monkeypatch.setenv("KG_PORT_RETRIES", "4321")
        monkeypatch.setenv("KG_IP", "1.1.1.1")
        monkeypatch.setenv("KG_AUTH_TOKEN", "fake-token")
        monkeypatch.setenv("KG_ALLOW_CREDENTIALS", "true")
        monkeypatch.setenv("KG_ALLOW_HEADERS", "Authorization")
        monkeypatch.setenv("KG_ALLOW_METHODS", "GET")
        monkeypatch.setenv("KG_ALLOW_ORIGIN", "*")
        monkeypatch.setenv("KG_EXPOSE_HEADERS", "X-Fake-Header")
        monkeypatch.setenv("KG_MAX_AGE", "5")
        monkeypatch.setenv("KG_BASE_URL", "/fake/path")
        monkeypatch.setenv("KG_MAX_KERNELS", "1")
        monkeypatch.setenv("KG_SEED_URI", "fake-notebook.ipynb")
        monkeypatch.setenv("KG_PRESPAWN_COUNT", "1")
        monkeypatch.setenv("KG_FORCE_KERNEL_NAME", "fake_kernel_forced")
        monkeypatch.setenv("KG_DEFAULT_KERNEL_NAME", "fake_kernel")
        monkeypatch.setenv("KG_KEYFILE", "/test/fake.key")
        monkeypatch.setenv("KG_CERTFILE", "/test/fake.crt")
        monkeypatch.setenv("KG_CLIENT_CA", "/test/fake_ca.crt")
        monkeypatch.setenv("KG_SSL_VERSION", "3")
        monkeypatch.setenv("KG_TRUST_XHEADERS", "false")

        app = KernelGatewayApp()

        assert app.port == 1234
        assert app.port_retries == 4321
        assert app.ip == "1.1.1.1"
        assert app.auth_token == "fake-token"
        assert app.allow_credentials == "true"
        assert app.allow_headers == "Authorization"
        assert app.allow_methods == "GET"
        assert app.allow_origin == "*"
        assert app.expose_headers == "X-Fake-Header"
        assert app.max_age == "5"
        assert app.base_url == "/fake/path"
        assert app.max_kernels == 1
        assert app.seed_uri == "fake-notebook.ipynb"
        assert app.prespawn_count == 1
        assert app.default_kernel_name == "fake_kernel"
        assert app.force_kernel_name == "fake_kernel_forced"
        assert app.keyfile == "/test/fake.key"
        assert app.certfile == "/test/fake.crt"
        assert app.client_ca == "/test/fake_ca.crt"
        assert app.ssl_version == 3
        assert app.trust_xheaders is False
        KernelGatewayApp.clear_instance()

    def test_trust_xheaders(self, monkeypatch):
        app = KernelGatewayApp()
        assert app.trust_xheaders is False
        monkeypatch.setenv("KG_TRUST_XHEADERS", "true")
        app = KernelGatewayApp()
        assert app.trust_xheaders is True
        KernelGatewayApp.clear_instance()

    def test_ssl_options(self, monkeypatch):
        app = KernelGatewayApp()
        ssl_options = app._build_ssl_options()
        assert ssl_options is None
        KernelGatewayApp.clear_instance()

        # Set all options
        monkeypatch.setenv("KG_CERTFILE", "/test/fake.crt")
        monkeypatch.setenv("KG_KEYFILE", "/test/fake.key")
        monkeypatch.setenv("KG_CLIENT_CA", "/test/fake.ca")
        monkeypatch.setenv("KG_SSL_VERSION", "42")
        app = KernelGatewayApp()
        ssl_options = app._build_ssl_options()
        assert ssl_options["certfile"] == "/test/fake.crt"
        assert ssl_options["keyfile"] == "/test/fake.key"
        assert ssl_options["ca_certs"] == "/test/fake.ca"
        assert ssl_options["cert_reqs"] == ssl.CERT_REQUIRED
        assert ssl_options["ssl_version"] == 42
        KernelGatewayApp.clear_instance()

        # Set few options
        monkeypatch.delenv("KG_KEYFILE")
        monkeypatch.delenv("KG_CLIENT_CA")
        monkeypatch.delenv("KG_SSL_VERSION")
        app = KernelGatewayApp()
        ssl_options = app._build_ssl_options()
        assert ssl_options["certfile"] == "/test/fake.crt"
        assert ssl_options["ssl_version"] == ssl.PROTOCOL_TLSv1_2
        assert "cert_reqs" not in ssl_options
        KernelGatewayApp.clear_instance()

    def test_load_notebook_local(self, monkeypatch):
        nb_path = os.path.join(RESOURCES, "weirdly%20named#notebook.ipynb")
        monkeypatch.setenv("KG_SEED_URI", nb_path)
        with open(nb_path) as nb_fh:
            nb_contents = nbformat.read(nb_fh, 4)

        app = KernelGatewayApp()
        app.init_io_loop()
        app.init_configurables()
        assert app.seed_notebook == nb_contents
        KernelGatewayApp.clear_instance()

    def test_start_banner(self, capsys):
        app = KernelGatewayApp()
        app.init_io_loop()
        app.init_configurables()
        app.start_app()
        log = capsys.readouterr()
        assert f"Jupyter Kernel Gateway {__version__}" in log.err
        KernelGatewayApp.clear_instance()
