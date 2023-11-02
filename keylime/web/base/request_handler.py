import tornado.web
import re
from keylime.web.base.router import Router

class RequestHandler(tornado.web.RequestHandler):
    def initialize(self, router):
        self.router = router

    def _process_request(self):
        method = self.request.method.lower()
        path = self.request.path

        matching_routes = (
            route for route in self.router.routes
            if route["method"] == method and Router.pattern_matches_path(route["pattern"], path)
        )

        first_match = next(matching_routes)
        pattern = first_match["pattern"]
        controller = first_match["controller"]
        controller_inst = self.router.controllers[controller]
        action = first_match["action"]

        if hasattr(controller_inst, action) and callable(getattr(controller_inst, action)):
            capture_groups = Router.capture_groups_from_path(pattern, path)
            action_func = getattr(controller_inst, action)
            action_func(self, capture_groups)
        else:
            raise ActionMissing(f"No action {action} exists in {controller.__name__}")

    def get(self):
        self._process_request()

    def head(self):
        self._process_request()

    def post(self):
        self._process_request()

    def delete(self):
        self._process_request()

    def patch(self):
        self._process_request()

    def put(self):
        self._process_request()

    def options(self):
        self._process_request()