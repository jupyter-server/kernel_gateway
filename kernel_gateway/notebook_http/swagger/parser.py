# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Parser for notebook cell Swagger API annotations."""

import json
from kernel_gateway.notebook_http.cell.parser import first_path_param_index, APICellParser
from traitlets import default, List
from traitlets.config.configurable import LoggingConfigurable

def _swaggerlet_from_markdown(cell_source):
    lines = cell_source.splitlines()
    if len(lines) > 2:
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[len(lines) - 1].startswith("```"):
            lines = lines[:-1]
    try:
        swagger_doc = json.loads(''.join(lines))
        if 'swagger' in swagger_doc and 'paths' in swagger_doc:
            return swagger_doc
    except ValueError:
        # not a swaggerlet
        pass
    return None

class SwaggerCellParser(LoggingConfigurable):
    notebook_cells = List()

    def __init__(self, *args, **kwargs):
        super(SwaggerCellParser, self).__init__(*args, **kwargs)
        self.api_cell_parser = APICellParser(*args, **kwargs)
        # cell:{swagger:,response:}
        self.api_cell_sources = dict()

        last_cell = None
        for cell in self.notebook_cells:
            if last_cell:
                # possible API cell preceded by doc
                if cell['cell_type'] == 'code' and last_cell['cell_type'] == 'markdown':
                    markdown_sources = last_cell['source'].splitlines(keepends=True)
                    if len(markdown_sources) > 2:
                        if markdown_sources[0].startswith("```"):
                            markdown_sources = markdown_sources[1:]
                        if markdown_sources[len(markdown_sources) - 1].startswith("```"):
                            markdown_sources = markdown_sources[:-1]
                    try:
                        swagger_doc = json.loads(''.join(markdown_sources))
                        if 'swagger' in swagger_doc and 'paths' in swagger_doc:
                            self.api_cell_sources[cell['source']] = {'swagger_doc':swagger_doc}
                    except ValueError:
                        # not a swaggerlet
                        pass
                # possible ResponseInfo cell preceded by API cell
                elif cell['cell_type'] == 'markdown' and last_cell['source'] in self.api_cell_sources and self.is_api_response_cell(cell['source']):
                    self.api_cell_sources[lastcell['source']]['response'] = cell['source']
            last_cell = cell

    def is_api_cell(self, cell_source):
        """Gets if the cell source is documented as an API endpoint.

        Parameters
        ----------
        cell_source
            Source from a notebook cell

        Returns
        -------
        bool
            True if cell is annotated as an API endpoint, or is itself
            a swaggerlet.
        """
        for source in self.api_cell_sources:
            if source == cell_source:
                return True
        return _swaggerlet_from_markdown(cell_source) is not None

    def is_api_response_cell(self, cell_source):
        """Gets if the cell source is annotated as defining API response
        metadata.

        Parameters
        ----------
        cell_source
            Source from a notebook cell

        Returns
        -------
        bool
            True if cell is annotated as ResponseInfo
        """
        match = self.api_cell_parser.kernelspec_api_response_indicator.match(cell_source)
        return match is not None

    def endpoints(self, source_cells, sort_func=first_path_param_index):
        """Gets the list of all annotated endpoint HTTP paths and verbs.

        Parameters
        ----------
        source_cells
            List of source strings from notebook cells
        sort_func
            Function by which to sort the endpoint list

        Returns
        -------
        list
            List of tuples with the endpoint str as the first element of each
            tuple and a dict mapping HTTP verbs to cell sources as the second
            element of each tuple
        """
        endpoints = {}
        for cell_source in source_cells:
            if cell_source in self.api_cell_sources:
                swagger_doc = self.api_cell_sources[cell_source]['swagger_doc']
                if swagger_doc:
                    endpoint = list(swagger_doc['paths'].keys())[0]
                    verb = list(swagger_doc['paths'][endpoint].keys())[0]
                    endpoints.setdefault(endpoint, {}).setdefault(verb, '')
                    endpoints[endpoint][verb] += cell_source + '\n'
        for cell_source in source_cells:
            swagger_doc = _swaggerlet_from_markdown(cell_source)
            if swagger_doc is not None:
                for endpoint in swagger_doc['paths'].keys():
                    for verb in swagger_doc['paths'][endpoint].keys():
                        if 'parameters' in swagger_doc['paths'][endpoint][verb]:
                            endpoint_with_param = endpoint
                            for parameter in swagger_doc['paths'][endpoint][verb]['parameters']:
                                endpoint_with_param = '/:'.join([endpoint_with_param, parameter['name']])
                            endpoints.setdefault(endpoint_with_param, {}).setdefault(verb, '')
                            endpoints[endpoint_with_param][verb] += cell_source + '\n'
                        else:
                            endpoints.setdefault(endpoint, {}).setdefault(verb, '')
                            endpoints[endpoint][verb] += cell_source + '\n'
        sorted_keys = sorted(endpoints, key=sort_func, reverse=True)
        return [(key, endpoints[key]) for key in sorted_keys]

    def get_cell_endpoint_and_verb(self, cell_source):
        """Gets the HTTP path and verb from an API cell annotation.

        If the cell is not annotated, returns (None, None)

        Parameters
        ----------
        cell_source
            Source from a notebook cell

        Returns
        -------
        tuple
            Endpoint str, HTTP verb str
        """
        endpoint = None
        verb = None
        swagger_doc = None
        if cell_source in self.api_cell_sources:
            swagger_doc = self.api_cell_sources[cell_source]['swagger_doc']
        if swagger_doc is None:
            swagger_doc = _swaggerlet_from_markdown(cell_source)
        if swagger_doc is not None:
            for endpoint in swagger_doc['paths'].keys():
                for verb in swagger_doc['paths'][endpoint].keys():
                    return (endpoint, verb.lower())
        return (None, None)

    def endpoint_responses(self, source_cells, sort_func=first_path_param_index):
        """Gets the list of all annotated ResponseInfo HTTP paths and verbs.

        Parameters
        ----------
        source_cells
            List of source strings from notebook cells
        sort_func
            Function by which to sort the endpoint list

        Returns
        -------
        list
            List of tuples with the endpoint str as the first element of each
            tuple and a dict mapping HTTP verbs to cell sources as the second
            element of each tuple
        """
        endpoints = {}
        for cell_source in source_cells:
            if self.is_api_response_cell(cell_source):
                matched = self.api_cell_parser.kernelspec_api_response_indicator.match(cell_source)
                uri = matched.group(2).strip()
                verb = matched.group(1)

                endpoints.setdefault(uri, {}).setdefault(verb, '')
                endpoints[uri][verb] += cell_source + '\n'
        return endpoints

    def get_path_content(self, cell_source):
        """Gets the operation description from an API cell annotation.

        Parameters
        ----------
        cell_source
            Source from a notebook cell

        Returns
        -------
        Object describing the supported operation. If the cell is not annotated,
        just minimal response output guidance.
        """
        swagger_doc = None
        for api_cell_source in self.api_cell_sources.keys():
            if api_cell_source == cell_source:
                swagger_doc = self.api_cell_sources[api_cell_source]['swagger_doc']
        if swagger_doc is None:
            swagger_doc = _swaggerlet_from_markdown(cell_source)
        if swagger_doc is not None:
            for endpoint in swagger_doc['paths'].keys():
                for verb in swagger_doc['paths'][endpoint].keys():
                    return swagger_doc['paths'][endpoint][verb]
        return {
            'responses' : {
                200 : { 'description': 'Success'}
            }
        }

def create_parser(*args, **kwargs):
    return SwaggerCellParser(*args, **kwargs)