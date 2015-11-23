# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
import tornado.web
import json
from queue import Empty
from .request_utils import *

class NotebookAPIHandler(tornado.web.RequestHandler):
    get_source = None
    put_source = None
    post_source = None
    delete_source = None
    kernel_client = None
    execution_timeout = 5
    def initialize(self, sources, kernel_client):
        self.kernel_client = kernel_client
        if 'GET' in sources:
            self.get_source = sources['GET']
        if 'POST' in sources:
            self.post_source = sources['POST']
        if 'PUT' in sources:
            self.put_source = sources['PUT']
        if 'DELETE' in sources:
            self.delete_source = sources['DELETE']

    def _send_code(self, code, block=True):
        # execute the get_source
        msg_id = self.kernel_client.execute(code)
        # This message will contain the status of code execution (failure or success)
        result_found = False
        iopub_message = None
        result = None
        try:
            while(result is None):
                iopub_message = self.kernel_client.get_iopub_msg(block=block, timeout=self.execution_timeout)
                # print(iopub_message)
                if iopub_message['header']['msg_type'] == 'execute_result':
                    result = iopub_message['content']['data']
        except Empty:
            print('Never found execute result')
            pass

        return result

    def _handle_request(self, source_code):
        if source_code is None:
            self.set_status(405)
            self.finish()
            return

        REQUEST = json.dumps({
            'body' : parse_body(self.request.body),
            'args' : parse_args(self.request.arguments),
            'path' : self.path_kwargs
        })
        request_code = "REQUEST = '"  + REQUEST + "'"

        print('REQUEST code is:\n ', request_code)
        # TODO: Need to figure out multil-lang assignment
        self._send_code(request_code, False)
        result = self._send_code(source_code)

        self.set_header('Content-Type', 'application/json')
        if result is not None:
            self.write(result)
        self.set_status(200)
        self.finish()

    def get(self, **kwargs):
        # execute the get_source
        self._handle_request(self.get_source)

    def post(self, **kwargs):
        # execute the post_source
        self._handle_request(self.post_source)

    def put(self, **kwargs):
        # execute the put_source
        print('in put method')
        self._handle_request(self.put_source)

    def delete(self, **kwargs):
        print('in delete method')
        # execute the delete_source
        self._handle_request(self.delete_source)
