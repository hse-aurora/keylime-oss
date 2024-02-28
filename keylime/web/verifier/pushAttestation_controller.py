import sys, time, json
from typing import Any, Dict

import tornado.web
import requests

from keylime.web.base import Controller
from keylime import web_util
from keylime.tpm import tpm_util
from keylime import (
    keylime_logging,
    config
)

from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from keylime.db.keylime_db import DBEngineManager, SessionManager
from keylime.db.verifier_db import VerfierMain, VerifierAttestations
from keylime.agentstates import AgentAttestState, AgentAttestStates
from keylime.attestationstatus import AttestationStatusEnum

logger = keylime_logging.init_logging("verifier")

#GLOBAL_POLICY_CACHE: Dict[str, Dict[str, str]] = {}

try:
    engine = DBEngineManager().make_engine("cloud_verifier")
except SQLAlchemyError as err:
    logger.error("Error creating SQL engine or session: %s", err)
    sys.exit(1) 

def get_session() -> Session:
    return SessionManager().make_session(engine)

class PushAttestation(Controller):
    # POST /v3.0/agents/:id/nonce
    # Generate nonce for push model


    """ def fetchAttestationValue(self, id):
        session = get_session()
        result = session.query(VerifierAttestations).filter_by(VerifierAttestations.agent_id == id).all()
        for agent_id_values in result:
            return agent_id_values """
        


    def attestations(self, req, id, **params):
        session = get_session()

        agent_id = id['id']
        att_result = session.query(VerifierAttestations).filter(VerifierAttestations.agent_id == agent_id).all()
        for att_values in att_result:
            att_values
        
        agent_result = session.query(VerfierMain).filter(VerifierAttestations.agent_id == agent_id).all()
        for agent_values in agent_result:
            agent_values
        
            
        #UPDATE ATTESTATION STATUS
        """ session.query(VerifierAttestations).filter(VerifierAttestations.agent_id == agent_id).update({VerifierAttestations.status: AttestationStatusEnum.FAILED})
        session.commit()
        updated = session.query(VerifierAttestations).filter(VerifierAttestations.agent_id == agent_id, VerifierAttestations.status == AttestationStatusEnum.FAILED).first()
        if updated:
            web_util.echo_json_response(req, 200, "Success", {"status":updated.status.to_json()})
        else:
            web_util.echo_json_response(req, 404)  """
        


        #web_util.echo_json_response(req, 200, "Success", {"nonce": agent_id_values.agent_id})

        current_timestamp = int(time.time())
        wait_time = agent_values.last_received_quote - config.getint("verifier","quote_interval")
        att_failed = session.query(VerifierAttestations).filter(VerifierAttestations.agent_id == agent_id, VerifierAttestations.status == AttestationStatusEnum.FAILED).first()
        
        if current_timestamp < wait_time:
            web_util.echo_json_response(req, 429)
        elif att_failed:
            web_util.echo_json_response(req, 503)
        else:
            nonce = tpm_util.random_password(20)
            nonce_created = int(time.time())
            nonce_lifetime = config.getint("verifier","nonce_lifetime")
            nonce_expires = nonce_created + nonce_lifetime
            session.query(VerifierAttestations).filter(VerifierAttestations.agent_id == agent_id).update({"nonce": nonce,
                                                                                                          "nonce_created": nonce_created,
                                                                                                          "nonce_expires":nonce_expires})
            session.commit()
            web_util.echo_json_response(req, 200,"nonce update", {"nonce":att_values.nonce, "offset":agent_values.next_ima_ml_entry})
    

    def get_attestations(self, req, id, **params):
        session = get_session()
        agent_id = id['id']
        atts = session.query(VerifierAttestations).filter(VerifierAttestations.agent_id == agent_id).all()
        for att in atts:
            atts_list = {
                "agent_id": att.agent_id,
                "nonce": att.nonce,
                "nonce_created": att.nonce_created,
                "nonce_expires": att.nonce_expires,
                "status": att.status.to_json(),
                "quote": att.quote,
                "quote_received": att.quote_received,
                "pcrs": att.pcrs,
                "next_ima_offset": att.next_ima_offset,
                "uefi_logs": att.uefi_logs,
            }
        web_util.echo_json_response(req, 200, "Success", {"result":atts_list})

    
    """ def update_attestations(self, req, id, **params):
        session = get_session()
        content_length = len(self.request.body)
        web_util.echo_json_response(req, 200, "Success", {"result":content_length})
        self. """





        
        

