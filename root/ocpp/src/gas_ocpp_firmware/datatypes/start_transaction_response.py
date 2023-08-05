from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class StartTransactionResponse:
    id_tag_info: Dict[str, Any]
    transaction_id: int
