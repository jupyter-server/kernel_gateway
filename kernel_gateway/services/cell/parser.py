"""An APICellParser to use notebook cells as REST API endpoints."""

# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import re
import sys


def first_path_param_index(endpoint):
    """Returns the index to the first path parameter for an endpoint.

    The index is not the string index, but rather where it is within the path.

    For example,
        first_path_param_index('/foo/:bar')     # returns 1
        first_path_param_index('/foo/quo/:bar') # return 2
        first_path_param_index('/foo/quo/bar')  # return sys.maxsize
    """
    index = sys.maxsize
    if endpoint.find(':') >= 0:
        index = endpoint.count('/', 0, endpoint.find(':')) - 1
    return index


class APICellParser(object):
    """A utility parser of Jupyter code cells to simplify using notebook
    cells as REST API endpoints.
    """
    kernelspec_comment_mapping = {
        None: '#',
        'scala': '//'
    }
    api_indicator = r'{}\s+(GET|PUT|POST|DELETE)\s+(\/.*)+'
    api_response_indicator = r'{}\s+ResponseInfo\s+(GET|PUT|POST|DELETE)\s+(\/.*)+'

    def __init__(self, kernelspec):
        try:
            prefix = self.kernelspec_comment_mapping[kernelspec]
        except KeyError:
            prefix = self.kernelspec_comment_mapping[None]
        self.kernelspec_api_indicator = re.compile(self.api_indicator.format(prefix))
        self.kernelspec_api_response_indicator = re.compile(self.api_response_indicator.format(prefix))

    def is_api_cell(self, cell_source):
        """Determines if the cell source is decorated to indicate an api cell"""
        match = self.kernelspec_api_indicator.match(cell_source)
        return match is not None

    def is_api_response_cell(self, cell_source):
        """Determines if the cell source is decorated to indicate an api response cell"""
        match = self.kernelspec_api_response_indicator.match(cell_source)
        return match is not None

    def get_cell_endpoint_and_verb(self, cell_source):
        """Parses a cell's source code and will return the endpoint and verb as a tuple"""
        endpoint = None
        verb = None
        matched = self.kernelspec_api_indicator.match(cell_source)
        if matched:
            endpoint = matched.group(2).strip()
            verb = matched.group(1)
        return endpoint, verb

    def endpoints(self, source_cells, sort_func=first_path_param_index):
        """Return a list of tuples containing the method+URI and the cell source"""
        endpoints = {}
        for cell_source in source_cells:
            if self.is_api_cell(cell_source):
                matched = self.kernelspec_api_indicator.match(cell_source)
                uri = matched.group(2).strip()
                verb = matched.group(1)

                endpoints.setdefault(uri, {}).setdefault(verb, '')
                endpoints[uri][verb] += cell_source + '\n'

        sorted_keys = sorted(endpoints, key=sort_func, reverse=True)
        return [(key, endpoints[key]) for key in sorted_keys]

    def endpoint_responses(self, source_cells, sort_func=first_path_param_index):
        """Return a list of tuples containing the method+URI and the cell source"""
        endpoints = {}
        for cell_source in source_cells:
            if self.is_api_response_cell(cell_source):
                matched = self.kernelspec_api_response_indicator.match(cell_source)
                uri = matched.group(2).strip()
                verb = matched.group(1)

                endpoints.setdefault(uri, {}).setdefault(verb, '')
                endpoints[uri][verb] += cell_source + '\n'
        return endpoints
