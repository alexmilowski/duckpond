import requests
import json
from flask import session,abort
from .app import app, users


def getCreativeWorks():
   url = app.config['SERVICE'] + 'content/'
   user = app.config['AUTH_SERVICE'].getUser(session['username'])
   req = requests.get(url,auth=requests.auth.HTTPBasicAuth(user['username'], user['password']))
   if req.status_code!=200:
      raise IOError("Cannot access service, status " + str(req.status_code))
   return json.loads(req.text)
