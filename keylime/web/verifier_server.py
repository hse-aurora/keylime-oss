from keylime.web.base.server import Server
from keylime.web.verifier.agents_controller import AgentsController

class VerifierServer(Server):
    
    def _routes(self):
        # _deprecated_v2_routes

        self.get("/v:version/agents/:id", AgentsController, "show")
        self.post("/v:version/agents", AgentsController, "create")
        self.delete("/v:version/agents/:id", AgentsController, "delete")
        self.post("/v:version/agents/:id/reactivate", AgentsController, "reactivate")
        self.post("/v:version/agents/:id/stop", AgentsController, "stop")

    # @version_range("1.0", "2.0")
    # def _deprecated_v2_routes(self):
    #     self.post("/v:version/agents/:id", AgentsController, "create")
    #     self.put("/v:version/agents/:id/reactivate", AgentsController, "reactivate")
    #     self.put("/v:version/agents/:id/stop", AgentsController, "stop")