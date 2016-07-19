# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Tests for swagger spec generation."""

import json
import unittest
from kernel_gateway.notebook_http.swagger.builders import SwaggerSpecBuilder
from kernel_gateway.notebook_http.cell.parser import APICellParser
from kernel_gateway.notebook_http.swagger.parser import SwaggerCellParser

class TestSwaggerBuilders(unittest.TestCase):
    """Unit tests the swagger spec builder."""
    def test_add_title_adds_title_to_spec(self):
        """Builder should store an API title."""
        expected = 'Some New Title'
        builder = SwaggerSpecBuilder(APICellParser(kernelspec='some_spec'))
        builder.set_title(expected)
        result = builder.build()
        self.assertEqual(result['info']['title'] ,expected,'Title was not set to new value')

    def test_add_cell_adds_api_cell_to_spec(self):
        """Builder should store an API cell annotation."""
        expected = {
            'get' : {
                'responses' : {
                    200 : { 'description': 'Success'}
                }
            }
        }
        builder = SwaggerSpecBuilder(APICellParser(kernelspec='some_spec'))
        builder.add_cell('# GET /some/resource')
        result = builder.build()
        self.assertEqual(result['paths']['/some/resource'] ,expected,'Title was not set to new value')

    def test_add_cell_does_not_add_non_api_cell_to_spec(self):
        """Builder should store ignore non- API cells."""
        builder = SwaggerSpecBuilder(APICellParser(kernelspec='some_spec'))
        builder.add_cell('regular code cell')
        result = builder.build()
        self.assertEqual(len(result['paths']) , 0,'Unexpected paths were found')

    def test_add_cell_adds_swaggerlet_cell_to_spec(self):
        """Builder should store an swagger documented cell."""
        builder = SwaggerSpecBuilder(SwaggerCellParser(kernelspec='some_spec'))
        expected = '''
        {
            "swagger": "2.0",
            "info" : {"version" : "0.0.0", "title" : "Default Title"},
            "paths": {
                "/some/resource": {
                    "get": {
                        "summary": "Get some resource",
                        "description": "Get some kind of resource?",
                        "operationId": "someResource",
                        "produces": [
                            "application/json"
                        ],
                        "responses": {
                            "200": {
                                "description": "a resource",
                                "schema": {
                                    "type": "object",
                                    "required": ["name"],
                                    "properties": {
                                        "name": {
                                            "type": "string"
                                        }
                                    }
                                }
                            },
                            "400": {
                                "description": "Error retrieving resources",
                                "schema": {
                                    "$ref": "#/definitions/error"
                                }
                            }
                        }
                    }
                }
            }
        }
        '''
        builder.add_cell(expected)
        result = builder.build()
        self.maxDiff = None
        self.assertEqual(result['paths']['/some/resource']['get']['description'], json.loads(expected)['paths']['/some/resource']['get']['description'], 'description was not preserved')
        self.assertEqual(json.dumps(result['paths']['/some/resource'], sort_keys=True), json.dumps(json.loads(expected)['paths']['/some/resource'], sort_keys=True), 'operations were not as expected')

    def test_add_undocumented_cell_does_not_add_non_api_cell_to_spec(self):
        """Builder should store ignore non- API cells."""
        builder = SwaggerSpecBuilder(SwaggerCellParser(kernelspec='some_spec'))
        builder.add_cell('regular code cell')
        result = builder.build()
        self.assertEqual(len(result['paths']) , 0, 'unexpected paths were found')
