from abc import ABC, abstractmethod
import asyncio
import tornado
from keylime.web.base.router import Router
from keylime.web.base.request_handler import RequestHandler
from keylime import config

# Contains everything needed to instantiate a HTTP server: request handlers, router logic, etc.
class Server(ABC):
    def __init__(self):
        self._port = config.get("verifier", "port")
        self._host = config.get("verifier", "ip")
        self._max_upload_size = config.getint("verifier", "max_upload_size", None, None)

        # Initialise empty router
        self._router = Router()

        # Add routes defined by the implementing class
        self._routes()

        # Create new Tornado app with request handler to process routes
        self.__tornado_app = tornado.web.Application([
            (r".*", RequestHandler, {"router": self.router})
        ])

        # Bind socket to user-configured port and address
        self.__tornado_sockets = tornado.netutil.bind_sockets(int(self.port), address=self.host)

        # TODO: Evaluate init_mtls function:
        # self.__ssl_ctx = web_util.init_mtls("verifier", logger=logger)
        self.__ssl_ctx = None

    async def start(self):
        """Instantiates and starts the HTTP server.
        This should be done once per process. When creating processes through forking, this method
        should be called after the fork.
        """

        self.__tornado_server = tornado.httpserver.HTTPServer(
            self.__tornado_app,
            ssl_options=self.__ssl_ctx,
            max_buffer_size=self.max_upload_size
        )

        self.__tornado_server.add_sockets(self.__tornado_sockets)

        await asyncio.Event().wait()

    @abstractmethod
    def _routes(self):
        pass

    def get(self, pattern, controller, action):
        self.router.append_route("get", pattern, controller, action)

    def post(self, pattern, controller, action):
        self.router.append_route("post", pattern, controller, action)

    def put(self, pattern, controller, action):
        self.router.append_route("put", pattern, controller, action)

    def patch(self, pattern, controller, action):
        self.router.append_route("patch", pattern, controller, action)

    def delete(self, pattern, controller, action):
        self.router.append_route("delete", pattern, controller, action)

    @property
    def port(self):
        return self._port

    @property
    def host(self):
        return self._host

    @property
    def max_upload_size(self):
        return self._max_upload_size

    @property
    def router(self):
        return self._router

