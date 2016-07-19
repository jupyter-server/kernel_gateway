# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Tests for notebook cell parsing."""

import unittest
import re
import sys
from kernel_gateway.notebook_http.swagger.parser import SwaggerCellParser
from kernel_gateway.notebook_http.cell.parser import APICellParser

class TestSwaggerAPICellParser(unittest.TestCase):
    """Unit tests the APICellParser class."""
    def test_is_api_cell(self):
        """Parser should correctly identify annotated API cells."""
        parser = SwaggerCellParser(kernelspec='some_unknown_kernel')
        self.assertTrue(parser.is_api_cell('{"swagger":"2.0", "paths": {"/yes": {"get": {}}}}'), 'API cell was not detected')
        self.assertFalse(parser.is_api_cell('no'), 'API cell was not detected')

    def test_endpoint_sort_default_strategy(self):
        """Parser should sort duplicate endpoint paths."""
        source_cells = [
            '{"swagger":"2.0", "paths": {"": {"post": {"parameters": [{"name": "foo"}]}}}}',
            '{"swagger":"2.0", "paths": {"/hello": {"post": {"parameters": [{"name": "foo"}]}}}}',
            '{"swagger":"2.0", "paths": {"/hello": {"get": {"parameters": [{"name": "foo"}]}}}}',
            '{"swagger":"2.0", "paths": {"/hello/world": {"put": {}}}}'
        ]
        parser = SwaggerCellParser(kernelspec='some_unknown_kernel')
        endpoints = parser.endpoints(source_cells)
        expected_values = ['/hello/world', '/hello/:foo', '/:foo']

        for index in range(0, len(expected_values)):
            endpoint, _ = endpoints[index]
            self.assertEqual(expected_values[index], endpoint, 'Endpoint was not found in expected order')

    def test_endpoint_sort_custom_strategy(self):
        """Parser should sort duplicate endpoint paths using a custom sort
        strategy.
        """
        source_cells = [
            '{"swagger":"2.0", "paths": {"/1": {"post": {}}}}',
            '{"swagger":"2.0", "paths": {"/+": {"post": {}}}}',
            '{"swagger":"2.0", "paths": {"/a": {"get": {}}}}'
        ]

        def custom_sort_fun(endpoint):
            index = sys.maxsize
            if endpoint.find('1') >= 0:
                return 0
            elif endpoint.find('a') >= 0:
                return 1
            else:
                return 2

        parser = SwaggerCellParser(kernelspec='some_unknown_kernel')
        endpoints = parser.endpoints(source_cells, custom_sort_fun)
        expected_values = ['/+', '/a', '/1']

        for index in range(0, len(expected_values)):
            endpoint, _ = endpoints[index]
            self.assertEqual(expected_values[index], endpoint, 'Endpoint was not found in expected order')


    def test_get_cell_endpoint_and_verb(self):
        """Parser should extract API endpoint and verb from cell annotations."""
        parser = SwaggerCellParser(kernelspec='some_unknown_kernel')
        endpoint, verb = parser.get_cell_endpoint_and_verb('{"swagger":"2.0", "paths": {"/foo": {"get": {}}}}')
        self.assertEqual(endpoint, '/foo', 'Endpoint was not extracted correctly')
        self.assertEqual(verb.lower(), 'get', 'Endpoint was not extracted correctly')
        endpoint, verb = parser.get_cell_endpoint_and_verb('{"swagger":"2.0", "paths": {"/bar/quo": {"post": {}}}}')
        self.assertEqual(endpoint, '/bar/quo', 'Endpoint was not extracted correctly')
        self.assertEqual(verb.lower(), 'post', 'Endpoint was not extracted correctly')

        endpoint, verb = parser.get_cell_endpoint_and_verb('some regular code')
        self.assertEqual(endpoint, None, 'Endpoint was not extracted correctly')
        self.assertEqual(verb, None, 'Endpoint was not extracted correctly')

    def test_endpoint_concatenation(self):
        """Parser should concatenate multiple cells with the same verb+path."""
        source_cells = [
            '{"swagger":"2.0", "paths": {"/foo": {"post": {"parameters": [{"name": "bar"}]}}}}',
            '{"swagger":"2.0", "paths": {"/foo": {"post": {"parameters": [{"name": "bar"}]}}}}',
            '{"swagger":"2.0", "paths": {"/foo": {"post": {}}}}',
            'ignored',
            '{"swagger":"2.0", "paths": {"/foo": {"get": {"parameters": [{"name": "bar"}]}}}}'
        ]
        parser = SwaggerCellParser(kernelspec='some_unknown_kernel')
        endpoints = parser.endpoints(source_cells)
        self.assertEqual(len(endpoints), 2)
        # for ease of testing
        endpoints = dict(endpoints)
        self.assertEqual(len(endpoints['/foo']), 1)
        self.assertEqual(len(endpoints['/foo/:bar']), 2)
        self.assertEqual(endpoints['/foo']['post'], '{"swagger":"2.0", "paths": {"/foo": {"post": {}}}}\n')
        self.assertEqual(endpoints['/foo/:bar']['post'], '{"swagger":"2.0", "paths": {"/foo": {"post": {"parameters": [{"name": "bar"}]}}}}\n{"swagger":"2.0", "paths": {"/foo": {"post": {"parameters": [{"name": "bar"}]}}}}\n')
        self.assertEqual(endpoints['/foo/:bar']['get'], '{"swagger":"2.0", "paths": {"/foo": {"get": {"parameters": [{"name": "bar"}]}}}}\n')

    def test_endpoint_response_concatenation(self):
        """Parser should concatenate multiple response cells with the same
        verb+path.
        """
        source_cells = [
            '# ResponseInfo POST /foo/:bar',
            '# ResponseInfo POST /foo/:bar',
            '# ResponseInfo POST /foo',
            'ignored',
            '# ResponseInfo GET /foo/:bar'
        ]
        parser = SwaggerCellParser(kernelspec='some_unknown_kernel')
        endpoints = parser.endpoint_responses(source_cells)
        self.assertEqual(len(endpoints), 2)
        # for ease of testing
        endpoints = dict(endpoints)
        self.assertEqual(len(endpoints['/foo']), 1)
        self.assertEqual(len(endpoints['/foo/:bar']), 2)
        self.assertEqual(endpoints['/foo']['POST'], '# ResponseInfo POST /foo\n')
        self.assertEqual(endpoints['/foo/:bar']['POST'], '# ResponseInfo POST /foo/:bar\n# ResponseInfo POST /foo/:bar\n')
        self.assertEqual(endpoints['/foo/:bar']['GET'], '# ResponseInfo GET /foo/:bar\n')
