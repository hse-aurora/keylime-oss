from abc import ABC, abstractmethod
from functools import wraps
import asyncio
import tornado
from keylime.web.base.route import Route
from keylime.web.base.action_handler import ActionHandler


class Server(ABC):
    """The Server abstract class provides a domain-specific language (DSL) for defining an HTTP server with a set of 
    specific endpoints. This is translated into a list of routes (see the ``Route`` class) which is ordered according to
    priority and can be matched against incoming requests based on their HTTP method and URL path.

    Example
    -------

    To use the Server class, inherit from it and implement the required ``_routes`` method::

        class ExampleServer(Server):
            def _routes(self):
                self._get("/", ExampleController, "example_action")
                # (Any additional routes...)

    Routes are defined by calling the ``self._get(...)``, ``self._post(...)``, ``self._put(...)``, etc. helper methods.
    These calls must happen within the ``_routes`` method or a method which is called by ``_routes``. Each helper method
    takes a path pattern, controller and action. For more details on these parameters, refer to the documentation for
    the ``Route`` class.
    
    In the event that multiple routes apply to a single request, routes defined earlier will take priority
    over routes defined later.

    Once a server is defined by subclassing Server as above, it can be used by creating a new instance and calling
    the ``start`` instance method::
    
        server = ExampleServer()
        server.start()

    Decorators
    ----------

    The Server class also provides decorators which can be used to modify routes defined using the helper methods,
    or generate additional routes automatically. These decorators can be applied directly to the routes defined
    in the ``_routes`` method or to a subset of routes by extracting them into their own method::

        class ExampleServer(Server):
            def _routes(self):
                self._v2_routes()
                self._get("/", HomeController, "index")

            @Server.version_scope(2)
            def _v2_routes(self):
                self._get("/agents", AgentsController, "index")
                self._get("/agents/:id", AgentsController, "show")

    The above example, in which ``@Server.version_scope(2)`` is applied to the ``_v2_routes`` method, is equivalent
    to defining all routes manually as follows:

        class ExampleServer(Server):
            def _routes(self):
                self._get("/v2/agents", AgentsController, "index")
                self._get("/v2.:minor/agents", AgentsController, "index")
                self._get("/v2/agents/:id", AgentsController, "show")
                self._get("/v2.:minor/agents/:id", AgentsController, "show")
                self._get("/", HomeController, "index")
    
    Notice that the ``"index"`` and ``"show"`` actions of ``AgentsController`` will now handle requests made to version
    2 of the API, regardless of whether a minor version is specified or not.
    """

    @staticmethod
    def version_scope(major_version: int):
        # Create a decorator which will scope routes to major_version
        def version_scope_decorator(func):
            # Create a wrapper function which will take the place of the decorated function (func)
            @wraps(func) # preserves the name and module of func when introspected
            def version_scope_wrapper(obj, *args, **kwargs):
                if not isinstance(obj, Server):
                    raise TypeError(
                        f"The @Server.version_scope(major_version) decorator can only be used on methods of a class "
                        f"which inherits from Server"
                    )

                # Get the routes defined at the time that the decorator is called
                initial_routes = obj.routes
                # Create a new list to hold the routes to be added to the Server
                new_routes_list = []
                # Call the decorated function and get the return value (typically None)
                value = func(obj, *args, **kwargs)

                # Iterate over routes created by the decorated function
                for route in obj.routes:
                    # Check that the current route is a route newly created by the decorated function
                    if route not in initial_routes:
                        # Define routes scoped to the API version specified by major_version
                        new_routes_list.extend([
                            Route(route.method, f"/v{major_version}{route.pattern}", route.controller, route.action),
                            Route(route.method, f"/v{major_version}.:minor{route.pattern}", route.controller, route.action)
                        ])

                # Replace the Server instance's list of routes with a new list consisting of the routes which were
                # present before func was called and the new routes scoped to major_version
                obj.__routes = initial_routes + new_routes_list

                # Return the return value of the decorated function in case it is something other than None
                return value
            return version_scope_wrapper
        return version_scope_decorator

    def __init__(self, host, port, max_upload_size=None):
        self._host = host
        self._port = port
        self._max_upload_size = max_upload_size

        # Initialise empty list of routes
        self.__routes = []

        # Add routes defined by the implementing class
        self._routes()

        # Create new Tornado app with request handler to process routes
        self.__tornado_app = tornado.web.Application([
            (r".*", ActionHandler, {"server": self})
        ])

        # Bind socket to user-configured port and address
        self.__tornado_sockets = tornado.netutil.bind_sockets(int(self.port), address=self.host)

        # TODO: Evaluate init_mtls function:
        # self.__ssl_ctx = web_util.init_mtls("verifier", logger=logger)
        self.__ssl_ctx = None

    async def start(self):
        """Instantiates and starts the HTTP server.

        This should be done once per process. When new processes are created by forking, this method
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

    def _get(self, pattern, controller, action):
        """Creates a new route to handle incoming GET requests issued for paths which match the given
        pattern. Must be called from a Server subclass's ``self._routes`` method.
        """
        self.__routes.append(Route("get", pattern, controller, action))

    def _head(self, pattern, controller, action):
        """Creates a new route to handle incoming HEAD requests issued for paths which match the given
        pattern. Must be called from a Server subclass's ``self._routes`` method.
        """
        self.__routes.append(Route("head", pattern, controller, action))

    def _post(self, pattern, controller, action):
        """Creates a new route to handle incoming POST requests issued for paths which match the given
        pattern. Must be called from a Server subclass's ``self._routes`` method.
        """
        self.__routes.append(Route("post", pattern, controller, action))

    def _put(self, pattern, controller, action):
        """Creates a new route to handle incoming PUT requests issued for paths which match the given
        pattern. Must be called from a Server subclass's ``self._routes`` method.
        """
        self.__routes.append(Route("put", pattern, controller, action))

    def _patch(self, pattern, controller, action):
        """Creates a new route to handle incoming PATCH requests issued for paths which match the given
        pattern. Must be called from a Server subclass's ``self._routes`` method.
        """
        self.__routes.append(Route("patch", pattern, controller, action))

    def _delete(self, pattern, controller, action):
        """Creates a new route to handle incoming DELETE requests issued for paths which match the given
        pattern. Must be called from a Server subclass's ``self._routes`` method.
        """
        self.__routes.append(Route("delete", pattern, controller, action))

    def _options(self, pattern, controller, action):
        """Creates a new route to handle incoming OPTIONS requests issued for paths which match the given
        pattern. Must be called from a Server subclass's ``self._routes`` method.
        """
        self.__routes.append(Route("options", pattern, controller, action))

    def first_matching_route(self, method, path):
        """Gets the highest-priority route which matches the given ``method`` and ``path``.
        """
        if method == None:
            matching_routes = (route for route in self.__routes if route.matches_path(path))
        else:
            matching_routes = (route for route in self.__routes if route.matches(method, path))

        try:
            return next(matching_routes)
        except StopIteration:
            return None

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
    def routes(self):
        return self.__routes.copy()