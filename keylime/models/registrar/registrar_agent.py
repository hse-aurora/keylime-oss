import base64
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from keylime.models.base import *
from keylime import crypto
from keylime import cert_utils
from keylime.tpm import tpm2_objects
from keylime.tpm.tpm_main import Tpm
from keylime.db.registrar_db import JSONPickleType
from keylime.json import JSONPickler

class RegistrarAgent(PersistableModel):

    @classmethod
    def _schema(cls):
        cls._persist_as("registrarmain")
        cls._id("agent_id", String(80))

        # The endorsement key (EK) of the TPM
        cls._field("ek_tpm", String(500))
        # The endorsement key (EK) certificate used to verify the TPM as genuine
        cls._field("ekcert", Text, nullable=True)
        # The attestation key (AK) used by Keylime to prepare TPM quotes
        cls._field("aik_tpm", String(500))
        # The initial attestation key (IAK) used when registering with a DevID
        cls._field("iak_tpm", String(500))
        # The signing key used as DevID
        cls._field("idevid_tpm", String(500))
        # The HMAC key used to verify the response produced by TPM2_ActivateCredential to bind the AK to the EK
        cls._field("key", String(45))
        # Indicates that the AK has successfully been bound to the EK
        cls._field("active", Boolean)
        # Indicates that the agent is running in a VM without an EKcert
        cls._field("virtual", Boolean)

        # The details used to establish connections to the agent when operating in pull mode
        cls._field("ip", String(15), nullable=True)
        cls._field("port", Integer, nullable=True)
        cls._field("mtls_cert", Text, nullable=True)

        # The number of times the agent has registered over its lifetime
        cls._field("regcount", Integer)

        cls._field("provider_keys", JSONPickleType(pickler=JSONPickler))

    @classmethod
    def empty(cls):
        agent = super().empty()
        agent.provider_keys = {}
        return agent

    def _prepare_ek(self):
        ekcert = self.changes.get("ekcert")

        if ekcert in (None, "emulator"):
            return

        try:
            cert = cert_utils.x509_der_cert(base64.b64decode(ekcert, validate=True))
            ek_pub = cert.public_key()
        except:
            self._add_error("ekcert", "must be a valid binary X.509 certificate encoded in Base64")
            return
        
        if not isinstance(ek_pub, (rsa.RSAPublicKey, ec.EllipticCurvePublicKey)):
            self._add_error("ekcert", "must contain a valid RSA or EC public key")
            return

        ek_tpm = base64.b64encode(tpm2_objects.ek_low_tpm2b_public_from_pubkey(ek_pub)).decode("utf-8")
        self.change("ek_tpm", ek_tpm)

    def _prepare_iak_idevid(self):
        # TODO: Add code to process IAK/IDevID
        return True

    def _prepare_status_flags(self):
        self.virtual = (self.ekcert == "virtual")

        if ("ek_tpm", "ekcert", "aik_tpm", "iak_tpm", "idevid_tpm") in self.changes:
            self.active = False

    def update(self, data):
        # Bind key-value pairs ('data') to those fields which are meant to be externally changeable
        self.cast_changes(data, [
            "agent_id", "ek_tpm", "ekcert", "aik_tpm", "iak_tpm", "idevid_tpm", "ip", "port", "mtls_cert"
        ])

        # Extract public EK from EK cert if possible
        self._prepare_ek()
        # Extract public IAK/IDevID from IAK/DevID certs if possible
        self._prepare_iak_idevid()
        # Determine and set 'virtual' and 'active' flags
        self._prepare_status_flags()
        
        # Validate values
        self.validate_required(["ek_tpm", "aik_tpm"])
        self.validate_base64(["ek_tpm", "ekcert", "aik_tpm", "iak_tpm", "idevid_tpm"])

    def produce_ak_challenge(self):
        ek_tpm = base64.b64decode(self.ek_tpm)
        aik_tpm = base64.b64decode(self.aik_tpm)

        try:
            result = Tpm.encrypt_aik_with_ek(self.agent_id, ek_tpm, aik_tpm)

            if not result:
                self._add_error("ek_tpm", "is not a valid TPM public key")
                return None
            
        except ValueError:
            self._add_error("aik_tpm", "is not a valid TPM public key")
            return None

        (challenge, key) = result
        self.change("key", key)
        return challenge.decode("utf-8")
    
    def verify_ak_response(self, response):
        expected_response = crypto.do_hmac(self.key.encode(), self.agent_id)

        result = (response == expected_response)

        self.change("active", result)
        return result


    def render(self, only=None):
        if not only:
            only = ["ek_tpm", "ekcert", "aik_tpm", "mtls_cert", "ip", "port", "regcount"]
            
            if self.virtual:
                only.append("provider_keys")

        return super().render(only)