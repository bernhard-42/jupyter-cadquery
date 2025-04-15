#
# Copyright 2025 Bernhard Walter
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import secrets

import orjson
from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.extension.application import ExtensionApp
from jupyter_server.extension.handler import ExtensionHandlerMixin

# ensure the Jupyter Cadquery comms routines will be loaded
os.environ["JUPYTER_CADQUERY"] = "1"
from ocp_vscode.backend import ViewerBackend
from ocp_vscode.comms import MessageType

BACKENDS = {}

API_KEY = secrets.token_urlsafe(32)


class MeasureHandler(ExtensionHandlerMixin, JupyterHandler):
    def post(self):
        viewer = self.get_body_argument("viewer")
        message = orjson.loads(self.get_body_argument("data"))

        apikey = self.get_body_argument("apikey")
        if apikey != API_KEY:
            self.log.error("Invalid API key")
            self.set_status(401, reason="Invalid API key")
            self.finish(orjson.dumps({"error": "Invalid API key"}))
            return

        if viewer is None:
            self.log.error("Unknown viewer")
            self.finish(orjson.dumps({"error": "Unknown viewer"}))
        elif message is None:
            self.log.error("Missing message")
            self.finish(orjson.dumps({"error": "Missing shape ID(s) or active Tool"}))
        else:
            backend = BACKENDS.get(viewer)
            if backend is None:
                self.log.error("Unknown viewer")
                self.finish(orjson.dumps({"error": "Unknown viewer"}))
            else:
                self.log.info(f"Identifiers received {message} for viewer {viewer}")
                result = backend.handle_event(message, MessageType.UPDATES)
                self.finish(orjson.dumps({"success": result}))


class ObjectsHandler(ExtensionHandlerMixin, JupyterHandler):
    def post(self):
        viewer = self.get_body_argument("viewer")
        data = orjson.loads(self.get_body_argument("data"))

        apikey = self.get_body_argument("apikey")
        if apikey != API_KEY:
            self.log.error("Invalid API key")
            self.set_status(401, reason="Invalid API key")
            self.finish(orjson.dumps({"error": "Invalid API key"}))
            return

        if viewer is None:
            self.log.error("Unknown viewer")
            self.finish(orjson.dumps({"error": "Unknown viewer"}))
        elif data is None:
            self.log.error("Missing objects")
            self.finish(orjson.dumps({"error": "Missing objects"}))
        else:
            BACKENDS[viewer] = ViewerBackend(port=0, jcv_id=viewer)
            BACKENDS[viewer].load_model(data["model"])
            self.log.info(f"Objects received for viewer {viewer}")
            self.finish(
                orjson.dumps({"success": f"Objects received for viewer {viewer}"})
            )


def wrapper(self, init_http):
    def init_httpserver():
        init_http()
        port = self.port
        os.environ["JUPYTER_PORT"] = str(port)
        os.environ["JUPYTER_CADQUERY_API_KEY"] = API_KEY
        self.log.info(f"JUPYTER_PORT={port}")
        self.log.info(f"JUPYTER_CADQUERY_API_KEY={API_KEY}")

    return init_httpserver


class JupyterCadqueryBackend(ExtensionApp):
    name = "jupyter_cadquery"
    static_paths = []
    template_paths = []

    def initialize_handlers(self):
        self.handlers.append((r"/measure", MeasureHandler))
        self.handlers.append((r"/objects", ObjectsHandler))

        init_http = self.serverapp.init_httpserver
        self.serverapp.init_httpserver = wrapper(self.serverapp, init_http)

    def initialize_settings(self):
        pass

    def initialize_templates(self):
        pass
