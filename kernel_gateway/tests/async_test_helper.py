# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

from tornado.httpclient import AsyncHTTPClient, HTTPResponse
from tornado.httpserver import HTTPServer
from tornado.testing import bind_unused_port, get_async_test_timeout
from tornado.web import Application

from typing import Any, Dict

from unittest import IsolatedAsyncioTestCase


class HTTPIsolatedAsyncioTestCase(IsolatedAsyncioTestCase):
    """A test case that starts up an HTTP server.

    Subclasses must override `get_app()`, which returns the
    `tornado.web.Application` (or other `.HTTPServer` callback) to be tested.
    Tests will typically use the provided ``self.http_client`` to fetch
    URLs from this server.

    Example, assuming the "Hello, world" example from the user guide is in
    ``hello.py``::

        import hello

        class TestHelloApp(AsyncHTTPTestCase):
            def get_app(self):
                return hello.make_app()

            def test_homepage(self):
                response = self.fetch('/')
                self.assertEqual(response.code, 200)
                self.assertEqual(response.body, 'Hello, world')

    That call to ``self.fetch()`` is equivalent to ::

        self.http_client.fetch(self.get_url('/'), self.stop)
        response = self.wait()

    which illustrates how AsyncTestCase can turn an asynchronous operation,
    like ``http_client.fetch()``, into a synchronous operation. If you need
    to do other asynchronous operations in tests, you'll probably need to use
    ``stop()`` and ``wait()`` yourself.

    .. deprecated:: 6.2
       `AsyncTestCase` and `AsyncHTTPTestCase` are deprecated due to changes
       in Python 3.10; see comments on `AsyncTestCase` for more details.
    """

    def setUp(self) -> None:
        super().setUp()
        sock, port = bind_unused_port()
        self.__port = port

        self.http_client = self.get_http_client()
        self._app = self.get_app()
        self.http_server = self.get_http_server()
        self.http_server.add_sockets([sock])

    def get_http_client(self) -> AsyncHTTPClient:
        return AsyncHTTPClient()

    def get_http_server(self) -> HTTPServer:
        return HTTPServer(self._app, **self.get_httpserver_options())

    def get_app(self) -> Application:
        """Should be overridden by subclasses to return a
        `tornado.web.Application` or other `.HTTPServer` callback.
        """
        raise NotImplementedError()

    def fetch(
        self, path: str, raise_error: bool = False, **kwargs: Any
    ) -> HTTPResponse:
        """Convenience method to synchronously fetch a URL.

        The given path will be appended to the local server's host and
        port.  Any additional keyword arguments will be passed directly to
        `.AsyncHTTPClient.fetch` (and so could be used to pass
        ``method="POST"``, ``body="..."``, etc).

        If the path begins with http:// or https://, it will be treated as a
        full URL and will be fetched as-is.

        If ``raise_error`` is ``True``, a `tornado.httpclient.HTTPError` will
        be raised if the response code is not 200. This is the same behavior
        as the ``raise_error`` argument to `.AsyncHTTPClient.fetch`, but
        the default is ``False`` here (it's ``True`` in `.AsyncHTTPClient`)
        because tests often need to deal with non-200 response codes.

        .. versionchanged:: 5.0
           Added support for absolute URLs.

        .. versionchanged:: 5.1

           Added the ``raise_error`` argument.

        .. deprecated:: 5.1

           This method currently turns any exception into an
           `.HTTPResponse` with status code 599. In Tornado 6.0,
           errors other than `tornado.httpclient.HTTPError` will be
           passed through, and ``raise_error=False`` will only
           suppress errors that would be raised due to non-200
           response codes.

        """
        if path.lower().startswith(("http://", "https://")):
            url = path
        else:
            url = self.get_url(path)
        return self.io_loop.run_sync(
            lambda: self.http_client.fetch(url, raise_error=raise_error, **kwargs),
            timeout=get_async_test_timeout(),
        )

    def get_httpserver_options(self) -> Dict[str, Any]:
        """May be overridden by subclasses to return additional
        keyword arguments for the server.
        """
        return {}

    def get_http_port(self) -> int:
        """Returns the port used by the server.

        A new port is chosen for each test.
        """
        return self.__port

    def get_protocol(self) -> str:
        return "http"

    def get_url(self, path: str) -> str:
        """Returns an absolute url for the given path on the test server."""
        return "%s://127.0.0.1:%s%s" % (self.get_protocol(), self.get_http_port(), path)

    async def asyncTearDown(self) -> None:
        self.http_server.stop()
        await self.http_server.close_all_connections()
        self.http_client.close()
        del self.http_server
        del self._app
        super().tearDown()
