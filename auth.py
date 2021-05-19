import os
import json
from flask import request
from functools import wraps
from jose import jwt
from urllib.request import urlopen

from models import Token

AUTH0_DOMAIN = os.environ['AUTH0_DOMAIN']
ALGORITHMS = os.environ['ALGORITHMS']
API_AUDIENCE = os.environ['API_AUDIENCE']

## AuthError Exception
'''
AuthError Exception
A standardized way to communicate auth failure modes
'''
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


## Auth Token
def get_token_auth_header():
    """Obtains the Access Token from the Authorization Header
    """
    bearer_token = 'Bearer ' + Token.query.one_or_none().jwt
    auth = request.headers.get("Authorization", None) if bearer_token is None else bearer_token 

    if not auth:
        raise AuthError({"code": "authorization_header_missing",
                        "description":
                            "Authorization header is expected"}, 401)

    parts = auth.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Authorization header must start with"
                            " Bearer"}, 401)
    elif len(parts) == 1:
        raise AuthError({"code": "invalid_header",
                        "description": "Token not found"}, 401)
    elif len(parts) > 2:
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Authorization header must be"
                            " Bearer token"}, 401)
    
    return parts[1]

def check_permissions(permission, payload):
    if 'permissions' not in payload:
        raise AuthError({
    'code': 'bad_request', 
    'description': 'Incorrect claims. Please, check for permissions.'
    }, 400)

    if permission not in payload['permissions']:
        raise AuthError({
    'code': 'forbidden_access', 
    'description': 'Incorrect claims. Please, check the permissions.'
    }, 403)

    return True

def verify_decode_jwt(token):
    jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
    jwks = json.loads(jsonurl.read())

    unverified_header = jwt.get_unverified_header(token)

    rsa_key = {}
    if 'kid' not in unverified_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    for key in jwks['keys']:
        if key['kid'] == unverified_header['kid']:
            rsa_key = {
                'kty': key['kty'],
                'kid': key['kid'],
                'use': key['use'],
                'n': key['n'],
                'e': key['e']
            }

    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer='https://' + AUTH0_DOMAIN + '/'
            )

        except jwt.ExpiredSignatureError:
            raise AuthError({
                'code': 'token_expired',
                'description': 'Token expired.'
            }, 401)

        except jwt.JWTClaimsError:
            raise AuthError({
                'code': 'invalid_claims',
                'description': 'Incorrect claims. Please, check the audience and issuer.'
            }, 401)
        except Exception:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to parse authentication token.'
            }, 400)
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Unable to find the appropriate key.'
            }, 400)
        
        return payload

def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            try:
                payload = verify_decode_jwt(token)
            except: 
                raise AuthError({
            'code': 'access_denied', 
            'description': 'Token could not be decoded.'
            }, 401)

            check_permissions(permission, payload)
            
            return f(payload, *args, **kwargs)

        return wrapper
    return requires_auth_decorator