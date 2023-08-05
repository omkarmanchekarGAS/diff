from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class AuthorizeResponse:
    id_tag_info: Dict[str, Any]  # of shape ocpp.v16.datatypes.IdTagInfo
