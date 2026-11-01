from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RefreshToken:
    token_hash: str
    user_id: str
    expires_at: datetime
    revoked: bool
