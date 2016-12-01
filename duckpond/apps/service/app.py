from flask import Flask, request, g, session, redirect, abort, Response
from datetime import datetime
from functools import wraps
import base64

app = Flask(__name__)
app.config.from_envvar('WEB_CONF')

def authenticate(f):
   @wraps(f)
   def wrapper(*args, **kwargs):
      v = request.headers.get('authorization')
      authenticated = False
      if v is not None and v.find('Basic ')==0:
         s = str(base64.b64decode(v[6:]),'utf-8')
         username = s[0:s.find(':')]
         password = s[s.find(':')+1:]
         info = app.config['AUTH_SERVICE'].authenticate(username,password);
         if info is not None:
            request.roles = info.get('roles')
            authenticated = True
      if v is not None and v.find('Bearer ')==0:
         roles = app.config['AUTH_SERVICE'].validateToken(v[7:])
         if roles is not None:
            authenticated = True
            request.roles = roles
      if authenticated:
         return f(*args, **kwargs)
      else:
         return Response(status=401, headers={'WWW-Authenticate': 'Basic realm="service"'})
   return wrapper

@app.before_request
@authenticate
def before_request():
   pass
