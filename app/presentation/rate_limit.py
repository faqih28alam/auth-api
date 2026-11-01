from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, headers_enabled=False)

REGISTER_LIMIT = "3/minute"
LOGIN_LIMIT = "5/minute"
REFRESH_LIMIT = "10/minute"
