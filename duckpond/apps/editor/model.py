import requests
import json
from flask import session, abort
from .app import app, users

def getAuth():
   user = app.config['AUTH_SERVICE'].getUser(session['username'])
   return requests.auth.HTTPBasicAuth(user['username'], user['password'])

def getCreativeWorks():
   url = app.config['SERVICE'] + 'content/'
   req = requests.get(url,auth=getAuth())
   if req.status_code!=200:
      raise IOError("Cannot access service, status " + str(req.status_code))
   return json.loads(req.text)

def createContent(typeName,genre,name,headline):
   url = app.config['SERVICE'] + 'content/'
   user = app.config['AUTH_SERVICE'].getUser(session['username'])
   headers = {'Content-Type' : 'application/ld+json'}
   data = {
      '@context' : 'http://schema.org/',
      '@type' : typeName,
      'genre' : genre,
      'name' : name,
      'headline' : headline
   }
   response = requests.post(url,auth=getAuth(),data=json.dumps(data),headers=headers)
   if response.status_code!=201:
      return (response.status_code,None)
   else:
      return (response.status_code,response.headers['Location'])

def deleteContent(id):
   url = app.config['SERVICE'] + 'content/' + id + '/'
   response = requests.delete(url,auth=getAuth())
   return response.status_code
