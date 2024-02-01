from keylime.web.base.server import Server
from keylime.web.registrar.agents_controller import AgentsController

class RegistrarServer(Server):
    
    def _routes(self):
        self._v2_routes()

    @Server.version_scope(2)
    def _v2_routes(self):
        self._get("/agents", AgentsController, "index")
        self._get("/agents/:agent_id", AgentsController, "show")
        self._post("/agents", AgentsController, "create")
        self._delete("/agents/:agent_id", AgentsController, "delete")
        self._post("/agents/:agent_id/activate", AgentsController, "activate")

        # These routes are kept for backwards compatibility but are less semantically correct according to RFC 9110
        self._post("/agents/:agent_id", AgentsController, "create")
        self._put("/agents/:agent_id/activate", AgentsController, "activate")