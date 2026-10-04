import hashlib
import time
from django.conf import settings


def is_bunny_video_id(value):
    if not value or value.startswith('pending://'):
        return False
    return True

def sign_embed_token(video_id, expires, token_security_key=None):
    """
    Fórmula oficial Bunny:
    SHA256_HEX(token_security_key + video_id + expiration)
    https://bunny.net/docs/stream/token-authentication
    """
    key = token_security_key if token_security_key is not None else settings.BUNNY_TOKEN_SECURITY_KEY
    payload = f"{key}{video_id}{expires}"
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def build_embed_url(video_id, now_ts=None):
    if not is_bunny_video_id(video_id):
        return None
    if not settings.BUNNY_LIBRARY_ID or not settings.BUNNY_TOKEN_SECURITY_KEY:
        return None

    
    now_ts = int(now_ts if now_ts is not None else time.time())
    expires = now_ts + settings.BUNNY_EMBED_TOKEN_TTL
    token = sign_embed_token(video_id, expires)
    host = settings.BUNNY_EMBED_HOST
    library_id = settings.BUNNY_LIBRARY_ID
    return (
        f'https://{host}/embed/{library_id}/{video_id}'
        f'?token={token}&expires={expires}'
    )

