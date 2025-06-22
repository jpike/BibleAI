## @package AgentResponse
## Response from a Bible study agent.

import dataclasses
from typing import Any

from BibleVerse import BibleVerse

## Response from a Bible study agent.
@dataclasses.dataclass
class AgentResponse:
    success: bool
    content: str
    verses_used: list[BibleVerse]
    metadata: dict[str, Any] 