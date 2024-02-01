from keylime.web.base import Controller
from keylime.models import RegistrarAgent
from keylime import keylime_logging

logger = keylime_logging.init_logging("registrar")


class AgentsController(Controller):
    # GET /v2[.:minor]/agents/
    def index(self, **params):
        results = RegistrarAgent.all_ids()

        self.respond(200, "Success", {"uuids": results})

    # GET /v2[.:minor]/agents/:agent_id/
    def show(self, agent_id, **params):
        agent = RegistrarAgent.get(agent_id)

        if not agent:
            self.respond(404, f"Agent with ID '{agent_id}' not found")
            return
        
        if not agent.active:
            self.respond(404, f"Agent with ID '{agent_id}' has not been activated")
            return

        self.respond(200, "Success", agent.render())
    
    # POST /v2[.:minor]/agents/[:agent_id]
    def create(self, agent_id, **params):
        agent = RegistrarAgent.get(agent_id) or RegistrarAgent.empty()
        agent.update({"agent_id": agent_id, **params})
        challenge = agent.produce_ak_challenge()

        if not challenge:
            self.respond(400, "Could not register agent because an invalid EK or AK was provided")
            return

        if not agent.changes_valid:
            self.respond(400, "Could not register agent with invalid data")
            return

        agent.commit_changes()
        self.respond(200, "Success", {"blob": challenge})

    # DELETE /v2[.:minor]/agents/:agent_id/
    def delete(self, agent_id, **params):
        agent = RegistrarAgent.get(agent_id)

        if not agent:
            self.respond(404, f"Agent with ID '{agent_id}' not found")
            return

        agent.delete()
        self.respond(200, "Success")
    
    # POST /v2[.:minor]/agents/:agent_id/activate/
    def activate(self, agent_id, auth_tag, **params):
        agent = RegistrarAgent.get(agent_id)

        if not agent:
            self.respond(404, f"Agent with ID '{agent_id}' not found")
            return
        
        accepted = agent.verify_ak_response(auth_tag)
        agent.commit_changes()
        self.respond(200, "Success")

        if not accepted:
            logger.warning(
                f"Auth tag '{auth_tag}' for agent '{agent_id}' does not match expected value. It will need to be "
                f"restarted in order to reattempt registration."
            )

