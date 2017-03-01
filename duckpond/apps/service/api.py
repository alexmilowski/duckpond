import io,json
import requests
import urllib
import uuid
from datetime import datetime
from pytz import timezone
from enum import Enum
from flask import render_template, redirect, request, url_for, escape, flash, g, abort, make_response, Response, stream_with_context
from .app import app

from duckpond.data.sparql import SPARQL

def curie(value):
   if value.find(':')<0:
      return "schema:"+value
   else:
      return value

def value(v,url=False):
   if type(v)==int:
      return str(v)
   if type(v)==float:
      return str(v)
   if type(v)==bool:
      return 'true' if v else 'false'
   if url:
      return '<' + v + '>'
   s = str(v)
   start = 0
   end = 0
   literal = io.StringIO()
   length = len(s)
   literal.write('"')
   for c in str(v):
      if c=='\\':
         literal.write('\\\\')
      elif c=='"':
         literal.write('\\"')
      elif c=='\u000a':
         literal.write('\\n')
      elif c=='\u000d':
         literal.write('\\r')
      else:
         literal.write(c)
   literal.write('"')
   return literal.getvalue()

def uri(s):
   return s[1:-1] if s[0]=='<' and s[-1]=='>' else s

def literal(s):
   return s[1:-1] if s[0]=='"' and s[-1]=='"' else s

def shorten(s):
   schema = 'http://schema.org/'
   return s[len(schema):] if s.find(schema)==0 else s

def expand(s):
   if s.find('schema:')==0:
      return 'http://schema.org/' + s[7:]
   if s.find(':')<0:
      return 'http://schema.org/' + s
   raise KeyError('Unknown prefix: '+s[0:s.find(':')])


class Service:

   class AuthMethod(Enum):
      basic = 1
      digest = 2

   def __init__(self,endpoints,cache=None):
      self.endpoints = {}
      self.endpoints['query'] = endpoints['query'] if 'query' in endpoints else None
      self.endpoints['update'] = endpoints['update'] if 'update' in endpoints else None
      self.cache = cache
      self.auth = self.authenticate('anonymous')

   def authenticate(self,user,password='',method=AuthMethod.basic):
      if (method is Service.AuthMethod.basic):
         self.auth = requests.auth.HTTPBasicAuth(user, password)
      elif (method is Service.AuthMethod.digest):
         self.auth = requests.auth.HTTPDigestAuth(user, password)
      else:
         raise Exception('Unsupported authentication method')

   def put(self,data,graph=None):
      uri = self.endpoints['update']
      if graph is not None:
         uri = uri + "?context=" + urllib.parse.quote('<'+graph+'>')

      if isinstance(data,str):
         data = data.encode('utf-8')

      req = requests.put(uri,data=data,headers={'content-type':'text/turtle; charset=utf-8'},auth=self.auth)

      #print(req.status_code)

      if (req.status_code<200 or req.status_code>=300):
         raise IOError('Cannot put data to uri <{}>, status={}'.format(uri,req.status_code))

   def post(self,data,graph=None):
      uri = self.endpoints['update']
      if graph is not None:
         uri = uri + "?context=" + urllib.parse.quote('<'+graph+'>')

      if isinstance(data,str):
         data = data.encode('utf-8')

      req = requests.post(uri,data=data,headers={'content-type':'text/turtle; charset=utf-8'},auth=self.auth)

      if (req.status_code<200 or req.status_code>=300):
         raise IOError('Cannot post data to uri <{}>, status={}'.format(uri,req.status_code))

   def exists(self,q,limit=None,graph=None):
      return self.query(q,limit=limit,graph=graph)

   def query(self,q,limit=None,graph=None):
      params = {'query':str(q)}
      if limit is not None:
         params['limit'] = limit
      if graph is not None:
         params['context'] = '<' + graph + '>'

      #print(str(q))

      req = requests.get(self.endpoints['query'],params=params,headers={'accept':'application/json'},auth=self.auth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         return data
      else:
         raise IOError('Cannot query to uri <{}>, status={}'.format(self.service,req.status_code))

   def update(self,q,limit=None,graph=None):
      params = {'query':str(q)}
      if limit is not None:
         params['limit'] = limit
      if graph is not None:
         params['context'] = '<' + graph + '>'

      #print(str(q))

      req = requests.post(self.endpoints['query'],params=params,headers={'accept':'application/json'},auth=self.auth)

      if (req.status_code>=200 or req.status_code<300):
         #print(req.text)
         data = json.loads(req.text)
         return data
      else:
         raise IOError('Cannot query to uri <{}>, status={}'.format(self.service,req.status_code))

   def retrieve(self,graph=None):
      uri = self.endpoints['update']
      params = {}
      if graph is not None:
         params['context'] = '<' + graph + '>'

      req = requests.get(uri,params=params,headers={'accept':'application/json'},auth=self.auth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         return data
      else:
         raise IOError('Cannot retrieve uri <{}>, status={}'.format(self.service,req.status_code))

   def deleteGraph(self,graph):
      uri = self.endpoints['update']
      params = {'context' : '<' + graph + '>' }

      req = requests.delete(uri,params=params,auth=self.auth)

      if (req.status_code>=200 or req.status_code<300):
         return True
      else:
         raise IOError('Cannot delete uri <{}>, status={}'.format(self.service,req.status_code))

   def deleteProperties(self,subject,property=None,object=None,graph=None):
      uri = self.endpoints['update']
      params = {'subj' : '<' + subject + '>' if subject[0]!='_' else subject }
      if property is not None:
         params['pred'] = '<' + expand(property) + '>'
      if object is not None:
         params['obj'] = object
      if graph is not None:
         params['context'] = '<' + graph + '>'

      req = requests.delete(uri,params=params,auth=self.auth)

      if (req.status_code>=200 or req.status_code<300):
         return True
      else:
         raise IOError('Cannot delete uri <{}>, status={}'.format(self.service,req.status_code))


class TurtleSerializer:
   def __init__(self):
      self.output = io.StringIO()
      self.urltypes = set(['url','contentUrl'])

   def __str__(self):
      return self.output.getvalue()

   def start(self):
      self.output.write('@prefix schema: <http://schema.org/> .\n')

   def end(self):
      return self.output.getvalue()

   def about(self,subject,data):
      if subject[0]=='_':
         self.output.write(subject)
         self.output.write('\n')
      else:
         self.output.write('<' + subject + '>\n')
      if '@type' in data:
         self.output.write('  a ' + curie(data['@type'] + ';\n'))
      first = True
      queue = []
      for name in data:
         if name == '@context' or name=='@type' or name=='@id':
            continue;
         if isinstance(data[name],dict):
            if not first:
               self.output.write(';\n')
            self.output.write('  ')
            self.output.write(curie(name))
            self.output.write(' ')
            if '@id' in data[name]:
               id = data[name]['@id']
               if id[0]=='_':
                  self.output.write(id)
               else:
                  self.output.write('<' + id + '>')
               queue.append(data[name])
            else:
               self.blankNode(data[name])
         elif isinstance(data[name],list):
            for obj in data[name]:
               if not first:
                  self.output.write(';\n')
               self.output.write('  ')
               self.output.write(curie(name))
               self.output.write(' ')
               if isinstance(obj,dict):
                  if '@id' in obj:
                     id = obj['@id']
                     if id[0]=='_':
                        self.output.write(id)
                     else:
                        self.output.write('<' + id + '>')
                     queue.append(obj)
                  else:
                     self.blankNode(obj)
               else:
                  self.output.write(value(obj,url=name in self.urltypes))
         else:
            if not first:
               self.output.write(';\n')
            self.output.write('  {0} {1}'.format(curie(name),value(data[name],url=name in self.urltypes)))
         first = False
      self.output.write('.\n')
      for o in queue:
         subject = o['@id']
         self.about(subject,o)
      #print(str(self))

   def blankNode(self,data):
      self.output.write('[')
      if '@type' in data:
         self.output.write(' a ' + curie(data['@type'] + ';\n'))
      first = True
      for name in data:
         if name == '@context' or name=='@type' or name=='@id':
            continue;
         if not first:
            self.output.write(';\n')
         if isinstance(data[name],dict):
            self.output.write('  ')
            self.output.write(curie(name))
            self.blankNode(data[name])
         else:
            self.output.write('  {0} {1}'.format(curie(name),value(data[name],url=name in self.urltypes)))
         first = False
      self.output.write(']')

def ask(data):
   turtle = io.StringIO()
   turtle.write('PREFIX schema: <http://schema.org/>\n')
   turtle.write('ASK { ?s \n')
   first = True
   for name in data:
      if name == '@context':
         continue;
      if not first:
         turtle.write(';\n')
      if name == '@type':
         turtle.write('  a '+curie(name))
      else:
         turtle.write('  {0} {1}'.format(curie(name),value(data[name],url=name=='url')))
      first = False
   turtle.write('\n}')
   s = turtle.getvalue()
   turtle.close()
   return s

def toJSONLD(subject,quads):
   objs = { subject : { '@context' : 'http://schema.org/', '@id' : subject}}

   toResolve = []
   for quad in quads:
      s = uri(quad[0])
      p = uri(quad[1])
      o = quad[2]
      obj = None
      if s in objs:
         obj = objs[s]
      else:
         obj = {'@id' : s}
         objs[s] = obj
      if p=='http://www.w3.org/1999/02/22-rdf-syntax-ns#type':
         obj['@type'] = shorten(uri(o))
      else:
         name = shorten(p)
         value = literal(uri(o))
         if name=='hasPart' or name=='associatedMedia' or name=='author' or value[0:2]=='_:':
            toResolve.append({ 'subject': obj, 'property': name, 'id': value})
         elif name in obj:
            if type(obj[name])!=list:
               l = [obj[name]]
               obj[name] = l
            obj[name].append(value)
         else:
            obj[name] = value

   for resolve in toResolve:
      name = resolve['property']
      target = resolve['subject']
      value = objs.get(resolve['id'])
      if value is None:
         continue
      if name=='hasPart' or name=='associatedMedia':
         if name not in target:
            target[name] = []
         target[name].append(value)
      elif name in target:
         if type(target[name])!=list:
            l = [target[name]]
            target[name] = l
         target[name].append(value)
      else:
         target[name] = value
   return objs[subject] if subject in objs else None

def now():
   return datetime.now(tz=timezone(app.config['TIMEZONE'] if 'TIMEZONE' in app.config else 'UTC')).isoformat()

def contentSubject(url):
   service = app.config['UPDATE_SERVICE']
   q = SPARQL() \
         .start({ 'schema' : 'http://schema.org/'}) \
         .select(['s']) \
         .where('?s schema:url <{}>'.format(url) )
   subjects = service.query(q)
   #print(subjects)
   return uri(subjects['values'][0][0]) if len(subjects['values'])>0 else None

def mediaSubject(s,url):
   service = app.config['UPDATE_SERVICE']
   q = SPARQL() \
         .start({ 'schema' : 'http://schema.org/'}) \
         .select(['s','p']) \
         .where('<{0}> ?p ?s . ?s schema:contentUrl <{1}>'.format(s,url) )
   subjects = service.query(q)
   #print(subjects)
   return (uri(subjects['values'][0][0]),uri(subjects['values'][0][1])) if len(subjects['values'])>0 else (None,None)

def mediaProperties(s,url,*names):
   service = app.config['UPDATE_SERVICE']
   expr = '<{0}> ?p ?s . ?s schema:contentUrl <{1}>'.format(s,url)
   for index,name in enumerate(names):
      expr += ';'
      expr += ' schema:'+name+' ?'+name
   q = SPARQL() \
         .start({ 'schema' : 'http://schema.org/'}) \
         .select(names) \
         .where(expr)
   #print(str(q))
   properties = service.query(q)
   return tuple(properties['values'][0]) if len(properties['values'])>0 else None

def subjectProperties(s,*names):
   service = app.config['UPDATE_SERVICE']
   expr = '<' + s + '>' if s[0]!='_' else s
   for index,name in enumerate(names):
      if index>0:
         expr += ';'
      expr += ' schema:'+name+' ?'+name
   q = SPARQL() \
         .start({ 'schema' : 'http://schema.org/'}) \
         .select(names) \
         .where(expr)
   #print(str(q))
   properties = service.query(q)
   return tuple(properties['values'][0]) if len(properties['values'])>0 else None

def jsonld_response(data):
   response = make_response(data)
   response.headers['Content-Type'] = "application/ld+json; charset=utf-8"
   return response

@app.route('/content/',methods=['GET','POST'])
def content():
   service = app.config['UPDATE_SERVICE']

   # GET returns a list of entities
   if request.method == 'GET':
      if 'reader' not in request.roles:
         abort(401)
      q = SPARQL() \
            .start({ 'schema' : 'http://schema.org/'}) \
            .select(['s','genre','type','name','headline','url','modified','published']) \
            .where('?s rdf:type ?type; schema:genre ?genre; schema:name ?name; schema:headline ?headline; schema:url ?url; schema:dateModified ?modified; . optional { ?s schema:datePublished ?published }'  )
      data = service.query(q)
      items = []
      for item in data['values']:
         ld = {
            '@context' : 'http://schema.org/',
            '@id' : uri(item[0]),
            '@type' : shorten(uri(item[2])),
            'genre' : literal(item[1]),
            'name' : literal(item[3]),
            'headline' : literal(item[4]),
            'url' : uri(item[5]),
            'dateModified' : literal(item[6])
         }
         if item[7] is not None:
            ld['datePublished'] = literal(item[7])
         items.append(ld)
      return jsonld_response(json.dumps(items))

   # POST creates an entity
   if request.method == 'POST':
      if 'writer' not in request.roles:
         abort(401)

      # Parse the incoming JSON-LD data
      force = request.headers['Content-Type'].startswith('application/ld+json')
      data = request.get_json(force=force)
      if data is None:
         abort(400)
      if 'name' not in data or \
         'genre' not in data or \
         '@type' not in data:
         abort(400)

      # Check to see if the name/genre already exists
      q = SPARQL() \
            .start({ 'schema' : 'http://schema.org/'}) \
            .select(['url']) \
            .where('?s schema:genre {}; schema:name {}; schema:url ?url'.format(value(data['genre']),value(data['name'])))
      existing = service.query(q)
      if len(existing['values'])>0:
         url = uri(existing['values'][0][0])
         id = url[url.rfind('/',0,-1)+1:-1]
         location = app.config['LOCATION_TEMPLATE'].format(**{'id' : id})
         return Response(status=409,headers={'Location' : location})
      if service.exists(ask({'genre' : data['genre'], 'name' : data['name']})):
         abort(409)

      subject = app.config['SUBJECT_TEMPLATE'].format(**data)
      id = str(uuid.uuid4())
      url = app.config['RESOURCE_TEMPLATE'].format(**{'id' : id})
      location = app.config['LOCATION_TEMPLATE'].format(**{'id' : id})
      data['url'] = url
      data['dateModified'] = now()

      turtle = TurtleSerializer()
      turtle.start()
      turtle.about(subject,data)
      service.put(turtle.end(),graph=url)
      return Response(status=201,headers={'Location' : location, 'Date-Modified' : data['dateModified']})

@app.route('/content/<id>/',methods=['GET','PUT','POST','DELETE'])
def content_item(id):
   service = app.config['UPDATE_SERVICE']
   url = app.config['RESOURCE_TEMPLATE'].format(**{'id' : id})
   subject = contentSubject(url)
   if subject == None:
      abort(404)
   if request.method == 'PUT':
      if 'writer' not in request.roles:
         abort(401)
      # Replace triples

      # Parse the incoming JSON-LD data
      force = request.headers['Content-Type'].startswith('application/ld+json')
      data = request.get_json(force=force)
      if data is None:
         abort(400)
      if 'name' not in data or \
         'genre' not in data or \
         '@type' not in data:
         abort(400)

      genre,name = subjectProperties(subject,'genre','name')

      # Check to see if the name/genre already exists
      if literal(genre)!=data['genre'] or literal(name)!=data['name']:
         if service.exists(ask({'genre' : data['genre'], 'name' : data['name']})):
            abort(409)

      subject = app.config['SUBJECT_TEMPLATE'].format(**data)
      data['url'] = url
      data['dateModified'] = now()

      turtle = TurtleSerializer()
      turtle.start()
      turtle.about(subject,data)

      # Update triples
      # TODO: transaction?
      service.deleteGraph(url)
      service.put(turtle.end(),graph=url)

      # Retrieve new representation
      quads = service.retrieve(graph=url)
      obj = toJSONLD(subject,quads)
      return jsonld_response(json.dumps(obj))

   if request.method == 'POST':
      if 'writer' not in request.roles:
         abort(401)
      force = request.headers['Content-Type'].startswith('application/ld+json')
      data = request.get_json(force=force)
      if data is None:
         abort(400)

      # Cannot rename subject with a post
      if 'name' in data or \
         'genre' in data:
         abort(400)

      data['dateModified'] = now()

      # Add triples
      turtle = TurtleSerializer()
      turtle.start()
      turtle.about(subject,data)
      service.post(turtle.end(),graph=url)

      # Retrieve new representation
      quads = service.retrieve(graph=url)
      obj = toJSONLD(subject,quads)
      return jsonld_response(json.dumps(obj))

   if request.method == 'GET':
      if 'reader' not in request.roles:
         abort(401)
      # Retrieve content
      quads = service.retrieve(graph=url)
      #print(quads)
      obj = toJSONLD(subject,quads)
      return jsonld_response(json.dumps(obj))

   if request.method == 'DELETE':
      if 'writer' not in request.roles:
         abort(401)
      service.deleteGraph(url)
      return Response(status=204)

@app.route('/content/<id>/<resource>',methods=['GET','PUT','DELETE'])
def content_item_resource(id,resource):
   return content_item_resource_property(id,resource,None)

@app.route('/content/<id>/<resource>;<property>',methods=['PUT'])
def content_item_resource_property(id,resource,property):
   service = app.config['UPDATE_SERVICE']
   url = app.config['RESOURCE_TEMPLATE'].format(**{'id' : id})
   resourceURL = url + resource
   parentSubject = contentSubject(url)
   if parentSubject == None:
      abort(404)
   subject,predicate = mediaSubject(parentSubject,resourceURL)
   #print(subject)
   if property is None:
      property = shorten(predicate)

   # allow PUT to create a resource
   if request.method == 'PUT':
      if 'writer' not in request.roles:
         abort(401)
      # Creating content
      contentType = request.headers['Content-Type']
      mediaObjectType = 'MediaObject'
      if contentType.find('image/')==0:
         mediaObjectType = 'ImageObject'
      elif contentType.find("video/")==0:
         mediaObjectType = 'VideoObject'
      if property is None:
         property = "associatedMedia"
      #print(request.headers)
      status = app.config['RESOURCE_SERVICE'].putResource(resourceURL,request.stream,content_type=contentType)
      if status>=200 and status<300:
         if subject is None:
            turtle = TurtleSerializer()
            turtle.start()
            turtle.about(parentSubject,{property : {"@type" : mediaObjectType, "contentUrl" : resourceURL, "fileFormat" : contentType, "name" : resource }})
            service.post(turtle.end(),graph=url)
            subject, *_ = mediaSubject(parentSubject,resourceURL)
         else:
            #print(subject)
            q = SPARQL() \
                  .start({ 'schema' : 'http://schema.org/'}) \
                  .withGraph(url) \
                  .delete('?media schema:fileFormat ?contentType') \
                  .insert('?media schema:fileFormat "{0}"'.format(contentType)) \
                  .where('?media schema:contentUrl <{0}>; schema:fileFormat ?contentType'.format(resourceURL) )
            service.update(q,graph=url)
      if status==204:
         status = 200
      if status>=200 and status<300:
         obj = {
            "@id" : subject,
            "@type" : mediaObjectType,
            "contentUrl" : resourceURL,
            "fileFormat" : contentType,
            "name" : resource
         }
         response = jsonld_response(json.dumps(obj))
         response.status_code = status
         return response
      else:
         abort(status)

   # when there is no subject for the associatedMedia, it does not exist
   if subject is None:
      abort(404)

   if request.method == 'GET':
      if 'reader' not in request.roles:
         abort(401)
      #print(subject)
      contentType, = mediaProperties(parentSubject,resourceURL,'fileFormat')
      #print(contentType)
      status,data,size = app.config['RESOURCE_SERVICE'].getResource(resourceURL)
      if status!=200:
         abort(status)
      response = Response(stream_with_context(data),mimetype=literal(contentType))
      response.headers['Content-Length'] = size
      return response

   if request.method == 'DELETE':
      if 'writer' not in request.roles:
         abort(401)
      # Retrieve content
      status = app.config['RESOURCE_SERVICE'].deleteResource(resourceURL)
      if status>=200 and status<300:
         # delete properties
         service.deleteProperties(parentSubject,object=subject,graph=url)
         service.deleteProperties(subject,graph=url)
      return Response(status=status)
