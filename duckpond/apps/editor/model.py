import requests
import json
import shutil
from tempfile import TemporaryFile
from flask import session, abort
from .app import app

def getAuth():
   user = app.config['AUTH_SERVICE'].getUser(session['username'])
   return requests.auth.HTTPBasicAuth(user['username'], user['password'])

def getContentList():
   url = app.config['SERVICE'] + 'content/'
   req = requests.get(url,auth=getAuth(),headers={'Connection' : 'close'})
   if req.status_code!=200:
      raise IOError('Cannot get content list from service, status {status}'.format(**{'status':req.status_code}))
   return json.loads(req.text)

def createContent(typeName,genre,name,headline):
   url = app.config['SERVICE'] + 'content/'
   user = app.config['AUTH_SERVICE'].getUser(session['username'])
   headers = {'Content-Type' : 'application/ld+json', 'Connection' : 'close'}
   data = {
      '@context' : 'http://schema.org/',
      '@type' : typeName,
      'genre' : genre,
      'name' : name,
      'headline' : headline
   }
   response = requests.post(url,auth=getAuth(),data=json.dumps(data),headers=headers)
   if response.status_code!=201:
      return (response.status_code,None,None)
   else:
      return (response.status_code,response.headers['Location'],response.headers['Date-Modified'])

def deleteContent(id):
   url = app.config['SERVICE'] + 'content/' + id + '/'
   response = requests.delete(url,auth=getAuth(),headers={'Connection' : 'close'})
   return response.status_code

def getContent(id):
   url = app.config['SERVICE'] + 'content/' + id + '/'
   response = requests.get(url,auth=getAuth(),headers={'Connection' : 'close'})
   if response.status_code==200:
      return json.loads(response.text)
   else:
      raise IOError('Cannot get content {id} from service, status {status}'.format(**{'status':response.status_code,'id':id}))

def updateContent(id,data):
   url = app.config['SERVICE'] + 'content/' + id + '/'
   headers = {'Content-Type' : 'application/ld+json', 'Connection' : 'close'}
   response = requests.put(url,auth=getAuth(),data=json.dumps(data),headers=headers)
   return (response.status_code,response.iter_content(chunk_size=10*1024),response.headers.get('content-type'))

def getContentResource(id,name):
   url = app.config['SERVICE'] + 'content/' + id + '/' + name
   response = requests.get(url,auth=getAuth(),stream = True,headers={'Connection' : 'close'})
   return (response.status_code,response.iter_content(chunk_size=10*1024),response.headers.get('content-type'))

def updateContentResource(id,name,content_type,data):
   url = app.config['SERVICE'] + 'content/' + id + '/' + name
   with TemporaryFile() as cached:
      shutil.copyfileobj(data,cached)
      size = cached.tell()
      cached.seek(0)
      headers = {'Content-Type' : content_type, 'Content-Length' : str(size), 'Connection' : 'close'}
      response = requests.put(url,auth=getAuth(),data=cached,headers=headers)
      return (response.status_code,response.iter_content(chunk_size=10*1024),response.headers.get('content-type'))

def uploadContentResource(id,property,name,content_type,content_length,data):
   url = app.config['SERVICE'] + 'content/' + id + '/' + name + ";" + property
   headers = {'Content-Type' : content_type, 'Content-Length' : str(content_length), 'Connection' : 'close'}
   response = requests.put(url,auth=getAuth(),data=data,headers=headers)
   return (response.status_code,response.iter_content(chunk_size=10*1024),response.headers.get('content-type'))

def deleteContentResource(id,name):
   url = app.config['SERVICE'] + 'content/' + id + '/' + name
   response = requests.delete(url,auth=getAuth(),headers={'Connection' : 'close'})
   return response.status_code
