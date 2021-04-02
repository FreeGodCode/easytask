from flask import request, g
from .jwt_util import verify_jwt


def jwt_authentication():
    """
    根据jwt验证用户身份
    """
    g.user_id = None
    g.use_token = False
    g.setreal = None
    g.mobile = None
    g.is_verified = False
    authorization = request.headers.get('Authorization')
    if authorization:
        g.use_token = True
        token = authorization
        payload = verify_jwt(token)
        if payload:
            g.user_id = payload.get('user_id')
            g.setreal = payload.get('setreal')
            g.mobile = payload.get('mobile')
            g.is_refresh_token = payload.get('refresh')
            g.is_verified = payload.get('verified', False)

