from enum import Enum
import json
from typing import Any

class AttestationStatusEnum(Enum):
    VERIFIED = "VERFIED"
    PENDING = "PENDING"
    FAILED = "FAILED"

    def to_json(self):
        return self.value
