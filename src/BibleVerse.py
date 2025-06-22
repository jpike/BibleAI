## @package BibleVerse
## Represents a single Bible verse with metadata.

import dataclasses
import re

## Represents a single Bible verse with metadata.
@dataclasses.dataclass
class BibleVerse:
    translation: str
    book: str
    chapter: int
    verse: int
    text: str
    osis_id: str
    
    ## Validate and clean the verse data.
    def __post_init__(self):
        self.text = self.text.strip()
        # Remove extra whitespace and normalize
        self.text = re.sub(r'\s+', ' ', self.text) 