from keylime.web.base.server import Server
from keylime.web.verifier.agents_controller import AgentsController
from keylime.web.verifier.pushAttestation_controller import PushAttestation

class VerifierServer(Server):
    
    def _routes(self):
        # _deprecated_v2_routes

        self.get("/v:version/agents/:id", AgentsController, "show")
        self.post("/v:version/agents", AgentsController, "create")
        self.delete("/v:version/agents/:id", AgentsController, "delete")
        self.post("/v:version/agents/:id/reactivate", AgentsController, "reactivate")
        self.post("/v:version/agents/:id/stop", AgentsController, "stop")
        self.post("/v:version/agents/:id/attestations", PushAttestation, "attestations")
        self.get("/v:version/agents/:id/attestations", PushAttestation, "get_attestations")
        self.put("/v:version/agents/:id/attestations/latest", PushAttestation, "update_attestations")

    # @version_range("1.0", "2.0")
    # def _deprecated_v2_routes(self):
    #     self.post("/v:version/agents/:id", AgentsController, "create")
    #     self.put("/v:version/agents/:id/reactivate", AgentsController, "reactivate")
    #     self.put("/v:version/agents/:id/stop", AgentsController, "stop")