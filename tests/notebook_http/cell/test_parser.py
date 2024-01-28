# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Tests for notebook cell parsing."""

import sys

from kernel_gateway.notebook_http.cell.parser import APICellParser


class TestAPICellParser:
    """Unit tests the APICellParser class."""

    def test_is_api_cell(self):
        """Parser should correctly identify annotated API cells."""
        parser = APICellParser(comment_prefix="#")
        assert parser.is_api_cell("# GET /yes"), "API cell was not detected"
        assert parser.is_api_cell("no") is False, "API cell was not detected"

    def test_endpoint_sort_default_strategy(self):
        """Parser should sort duplicate endpoint paths."""
        source_cells = [
            "# POST /:foo",
            "# POST /hello/:foo",
            "# GET /hello/:foo",
            "# PUT /hello/world",
        ]
        parser = APICellParser(comment_prefix="#")
        endpoints = parser.endpoints(source_cells)
        expected_values = ["/hello/world", "/hello/:foo", "/:foo"]

        for index in range(len(expected_values)):
            endpoint, _ = endpoints[index]
            assert expected_values[index] == endpoint, "Endpoint was not found in expected order"

    def test_endpoint_sort_custom_strategy(self):
        """Parser should sort duplicate endpoint paths using a custom sort
        strategy.
        """
        source_cells = ["# POST /1", "# POST /+", "# GET /a"]

        def custom_sort_fun(endpoint):
            _ = sys.maxsize
            if endpoint.find("1") >= 0:
                return 0
            elif endpoint.find("a") >= 0:
                return 1
            else:
                return 2

        parser = APICellParser(comment_prefix="#")
        endpoints = parser.endpoints(source_cells, custom_sort_fun)
        expected_values = ["/+", "/a", "/1"]

        for index in range(len(expected_values)):
            endpoint, _ = endpoints[index]
            assert expected_values[index] == endpoint, "Endpoint was not found in expected order"

    def test_get_cell_endpoint_and_verb(self):
        """Parser should extract API endpoint and verb from cell annotations."""
        parser = APICellParser(comment_prefix="#")
        endpoint, verb = parser.get_cell_endpoint_and_verb("# GET /foo")
        assert endpoint, "/foo" == "Endpoint was not extracted correctly"
        assert verb, "GET" == "Endpoint was not extracted correctly"
        endpoint, verb = parser.get_cell_endpoint_and_verb("# POST /bar/quo")
        assert endpoint, "/bar/quo" == "Endpoint was not extracted correctly"
        assert verb, "POST" == "Endpoint was not extracted correctly"

        endpoint, verb = parser.get_cell_endpoint_and_verb("some regular code")
        assert endpoint is None, "Endpoint was not extracted correctly"
        assert verb is None, "Endpoint was not extracted correctly"

    def test_endpoint_concatenation(self):
        """Parser should concatenate multiple cells with the same verb+path."""
        source_cells = [
            "# POST /foo/:bar",
            "# POST /foo/:bar",
            "# POST /foo",
            "ignored",
            "# GET /foo/:bar",
        ]
        parser = APICellParser(comment_prefix="#")
        endpoints = parser.endpoints(source_cells)
        assert len(endpoints) == 2
        # for ease of testing
        endpoints = dict(endpoints)
        assert len(endpoints["/foo"]) == 1
        assert len(endpoints["/foo/:bar"]) == 2
        assert endpoints["/foo"]["POST"] == "# POST /foo\n"
        assert endpoints["/foo/:bar"]["POST"] == "# POST /foo/:bar\n# POST /foo/:bar\n"
        assert endpoints["/foo/:bar"]["GET"] == "# GET /foo/:bar\n"

    def test_endpoint_response_concatenation(self):
        """Parser should concatenate multiple response cells with the same
        verb+path.
        """
        source_cells = [
            "# ResponseInfo POST /foo/:bar",
            "# ResponseInfo POST /foo/:bar",
            "# ResponseInfo POST /foo",
            "ignored",
            "# ResponseInfo GET /foo/:bar",
        ]
        parser = APICellParser(comment_prefix="#")
        endpoints = parser.endpoint_responses(source_cells)
        assert len(endpoints) == 2
        # for ease of testing
        endpoints = dict(endpoints)
        assert len(endpoints["/foo"]) == 1
        assert len(endpoints["/foo/:bar"]) == 2
        assert endpoints["/foo"]["POST"] == "# ResponseInfo POST /foo\n"
        assert (
            endpoints["/foo/:bar"]["POST"]
            == "# ResponseInfo POST /foo/:bar\n# ResponseInfo POST /foo/:bar\n"
        )
        assert endpoints["/foo/:bar"]["GET"] == "# ResponseInfo GET /foo/:bar\n"
