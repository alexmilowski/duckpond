import requests
import json,io,os
import logging
from enum import Enum
import urllib
from .sparql import SPARQL

def strip(value):
   if value is None:
      return value
   elif value[0]=='"' and value[-1]=='"':
      value = value[1:-1]
      if value[0]=='<' and value[-1]=='>':
         return value[1:-1]
      else:
         return value
   elif value[0]=='<':
      return value[1:-1]
   else:
      return value

def literal(value):
   value = strip(value)
   return value.replace('\\"','"')

class Facet:
   def __init__(self,id,name,type = 'xsd:string'):
      self.id = id
      self.name = name
      self.type = type

   def __str__(self):
      return self.name

   def toLiteral(self,value):
      if self.type=='xsd:anyURI':
         return '<' + value + '>'
      else:
         return '"' + value + '"'

orgSchema = [
   Facet('type','schema:BlogPosting',None),
   Facet('order','schema:datePublished','xsd:dateTime'),
   Facet('title','schema:headline'),
   Facet('summary','schema:description'),
   Facet('name','schema:name'),
   Facet('genre','schema:genre'),
   Facet('resource','schema:hasPart','schema:MediaObject'),
   Facet('category','schema:keywords'),
   Facet('contentUrl','schema:contentUrl'),
   Facet('fileFormat','schema:fileFormat'),
   Facet('associatedMedia','schema:associatedMedia','schema:MediaObject'),

   Facet('Article','schema:Article'),
   Facet('MediaObject','schema:MediaObject'),
   Facet('ImageObject','schema:ImageObject'),
   Facet('ImageGallery','schema:ImageGallery')
]

def criteriaConditions(pond,criteria,subjectVar='s'):
   conditions = io.StringIO()
   def addLiteralCriteria(property,value):
      conditions.write('\n?{0} {1} "{2}" .'.format(subjectVar,property,value))
   def addURICriteria(property,value):
      conditions.write('\n?{0} {1} <{2}> .'.format(subjectVar,property,value))
   for property in criteria.keys():
      value = criteria[property]
      if property.find(':')<0:
         property = 'schema:' + property
      if type(value)==dict:
         literal = value.get('@value')
         typename = value.get('@type')
         if literal is not None:
            if typename=='xsd:anyURI' or pond.isURIProperty(property):
               addURICriteria(property,literal)
            else:
               addLiteralCriteria(property,literal)
      elif pond.isURIProperty(property):
         addURICriteria(property,value)
      else:
         addLiteralCriteria(property,value)
   return conditions.getvalue()

class Pond:

   class AuthMethod(Enum):
      basic = 1
      digest = 2

   class ResourceType(Enum):
      uri = 1
      stream = 2
      local = 3

   def __init__(self,service,cache=None,facets=None,graphs=None):
      self.logger = logging.getLogger(__name__)
      self.logger.setLevel(logging.DEBUG)
      self.logger.debug('Debug log for '+__name__)
      self.service = service
      self.cache = cache
      self.serviceAuth = self.authenticate('anonymous')
      self.resourceAuth = None
      self.resourceToken = None
      self.prefixes = { 'schema' : 'http://schema.org/'}
      self.graphs = []
      self.propertyTypes = {
         'url' : 'xsd:anyURI',
         'contentUrl' : 'xsd:anyURI',
         'isBasedOn' : 'xsd:anyURI',
         'isBasedOnUrl' : 'xsd:anyURI'
      }
      if graphs is not None:
         for graph in graphs:
            self.graphs.append(graph)

      self.facets = {}
      for facet in orgSchema:
         self.facets[facet.id] = facet
      if facets is not None:
         for facet in facets:
            self.facets[facet.id] = facet

   def isURIProperty(self,property):
      typename = self.propertyTypes.get(property)
      return True if typename=='xsd:anyURI' else False

   def getProlog(self):
      glob = io.StringIO()
      for key in self.prefixes:
         glob.write('prefix {}: <{}>'.format(key,self.prefixes[key]))
      return glob.getvalue()

   def setProxyCache(self,proxy,base):
      self.cache = { 'proxy': proxy, 'base':base }

   def authenticate(self,user,password='',method=AuthMethod.basic):
      if (method is Pond.AuthMethod.basic):
         self.auth = requests.auth.HTTPBasicAuth(user, password)
      elif (method is Pond.AuthMethod.digest):
         self.auth = requests.auth.HTTPDigestAuth(user, password)
      else:
         raise Exception('Unsupported authentication method')

   def defaultParameters(self):
      params = {}
      return params

   def mergeParameters(self,requestParameters):
      params = self.defaultParameters()
      for param in requestParameters.keys():
         params[param] = requestParameters[param]
      return params

   def getGraphs(self):
      named = ''
      for graph in self.graphs:
         named = named + 'from named <' + graph +'> '
      return named

   def facet(self,name,value = None):
      if type(value)==str:
         value = self.facets[value]
      return value if value is not None else self.facets[name]

   def currentEntity(self,entity = None,order = None,title = None, summary = None, criteria = None, name = None, genre = None):

      entityType = self.facet('type',entity)
      orderFacet = self.facet('order',order)
      titleFacet = self.facet('title',title)
      summaryFacet = self.facet('summary',summary)
      nameFacet = self.facet('name',name)
      genreFacet = self.facet('genre',genre)

      expr = '?s rdf:type {0}; {1} ?ordering; {2} ?title; {4} ?name; {5} ?genre; . optional {{ ?s {3} ?summary . }}'.format(entityType,orderFacet,titleFacet,summaryFacet,nameFacet,genreFacet)
      if criteria is not None:
         expr = expr + criteriaConditions(self,criteria)

      q = SPARQL() \
            .start(self.prefixes) \
            .select(['s','title','summary','ordering','name','genre']) \
            .fromGraphs(self.graphs) \
            .where(expr) \
            .orderBy('desc(?ordering)')
      if self.logger.isEnabledFor(logging.DEBUG):
         self.logger.debug(str(q))
      params = self.mergeParameters({'limit':1,'query':str(q)})

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         #print(req.text)
         data = json.loads(req.text)
         if len(data['values']) == 0:
            return None
         subject = strip(data['values'][0][0])
         title = literal(data['values'][0][1])
         summary = literal(data['values'][0][2]) if data['values'][0][2] is not None else None
         dateTime = strip(data['values'][0][3])
         nameValue = strip(data['values'][0][4])
         genreValue = strip(data['values'][0][5])
         date,time = dateTime.split('T') # Need to check that is xsd:dateTime
         return (subject,title,summary,date,time,nameValue,genreValue)
      else:
         raise IOError('Cannot post data to uri <{}>, status={}'.format(self.service,req.status_code))

   def getEntityByName(self,value,name=None,title=None,order=None,summary=None,criteria=None,genre=None):
      nameFacet = self.facet('name',name)
      orderFacet = self.facet('order',order)
      titleFacet = self.facet('title',title)
      summaryFacet = self.facet('summary',summary)
      genreFacet = self.facet('genre',genre)

      expr = '?s {0} "{1}"; {2} ?ordering; {3} ?title; {5} ?genre; . optional {{ ?s {4} ?summary . }}'.format(nameFacet,value,orderFacet,titleFacet,summaryFacet,genreFacet)
      if criteria is not None:
         expr = expr + criteriaConditions(self,criteria)

      q = SPARQL() \
            .start(self.prefixes) \
            .select(['s','title','summary','ordering','genre']) \
            .fromGraphs(self.graphs) \
            .where(expr) \
            .orderBy('desc(?ordering)')
      if self.logger.isEnabledFor(logging.DEBUG):
         self.logger.debug(str(q))
      params = self.mergeParameters({'limit':1,'query':str(q)})

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         #print(req.text)
         data = json.loads(req.text)
         if len(data['values']) == 0:
            return None
         subject = strip(data['values'][0][0])
         title = literal(data['values'][0][1])
         summary = literal(data['values'][0][2]) if data['values'][0][2] is not None else None
         dateTime = strip(data['values'][0][3])
         date,time = dateTime.split('T') # Need to check that is xsd:dateTime
         genreValue = strip(data['values'][0][4])
         return (subject,title,summary,date,time,value,genreValue)
      else:
         raise IOError('Cannot query uri <{}>, status={}'.format(self.service,req.status_code))

   def proxyURL(self,resource):
      uri = resource
      if not self.cache==None and 'proxy' in self.cache and 'base' in self.cache:
         base = self.cache['base']
         relative = resource[resource.index(base) + len(base):]
         uri = self.cache['proxy'] + relative
      if not self.cache==None and 'dir' in self.cache:
         relative = resource
         if 'base' in self.cache:
            base = self.cache['base']
            relative = resource[resource.index(base) + len(base):]
         uri = 'file://' + os.path.join(os.path.abspath(self.cache['dir']),relative)
      return uri

   def getResourceText(self,resource,authorization=None):

      uri = self.proxyURL(resource)

      self.logger.debug(uri)

      if self.cache==None or uri[0:5]=='http:' or uri[0:6]=='https:':
         headers = {}
         if self.resourceToken is not None:
            headers['Authorization'] = 'Bearer ' + self.resourceToken
         req = requests.get(uri,auth=self.resourceAuth,headers=headers)
         if (req.status_code == 200):
            contentType = req.headers.get('Content-Type')
            encoding = 'UTF-8'
            if contentType is not None:
               param = contentType.find('charset=')
               if param>0:
                  encoding = contentType[param+8:]
            text = req.content.decode(encoding)
            return text
         else:
            raise IOError('Cannot get <{}>, status={}'.format(uri,req.status_code))
      elif uri[0:7]=='file://':
         entryFile = open(uri[7:], mode='r', encoding='utf-8')
         entry = entryFile.read()
         entryFile.close()
         return entry
      else:
         entryFile = open(uri, mode='r', encoding='utf-8')
         entry = entryFile.read()
         entryFile.close()
         return entry

   def getResource(self,resource):

      uri = self.proxyURL(resource)

      if self.cache!=None and 'redirect' in self.cache and self.cache['redirect']:
         return (Pond.ResourceType.uri,uri,303)
      if self.cache==None or uri[0:5]=='http:' or uri[0:6]=='https:':
         headers = {}
         if self.resourceToken is not None:
            headers['Authorization'] = 'Bearer ' + self.resourceToken
         req = requests.get(uri, stream = True,auth=self.resourceAuth,headers=headers)
         return (Pond.ResourceType.stream,req.iter_content(20*1024),req.headers['content-type'],req.headers.get('content-length'))
      elif uri[0:7]=='file://':
         location = uri[7:]
         return (Pond.ResourceType.local,location,None,os.path.getsize(location))
      else:
         return (Pond.ResourceType.local,uri,None,os.path.getsize(uri))

   def relatedEntityByOrder(self,value,previous = True,limit = 1,singleton = False,entity = None,order = None,title = None, summary = None, criteria = None, name=None, genre=None):
      entityType = self.facet('type',entity)
      orderFacet = self.facet('order',order)
      titleFacet = self.facet('title',title)
      summaryFacet = self.facet('summary',summary)
      nameFacet = self.facet('name',name)
      genreFacet = self.facet('genre',genre)
      expr = '?s rdf:type {0}; {1} ?ordering; {2} ?title; {4} ?name; {5} ?genre; . optional {{ ?s {3} ?summary . }}'.format(entityType,orderFacet,titleFacet,summaryFacet,nameFacet,genreFacet) \
             + ' FILTER( ?ordering ' + ('<' if previous else '>') + ' ' + orderFacet.toLiteral(value) + ' )'
      if criteria is not None:
         expr = expr + criteriaConditions(self,criteria)
      q = SPARQL() \
            .start(self.prefixes) \
            .select(['s','title','summary','ordering','name','genre']) \
            .fromGraphs(self.graphs) \
            .where(expr ) \
            .orderBy('desc(?ordering)' if previous else 'asc(?ordering)')
      if self.logger.isEnabledFor(logging.DEBUG):
         self.logger.debug(str(q))
      params = self.mergeParameters({'limit':limit,'query':str(q)})

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         values = data['values']
         if len(values)==0:
            return None
         elif len(values)==1 and not singleton:
            row = values[0]
            subjectValue = strip(row[0])
            titleValue = literal(row[1])
            summaryValue = literal(row[2]) if row[2] is not None else None
            date,time = strip(row[3]).split('T')
            nameValue = strip(row[4])
            genreValue = strip(row[5])
            return (subjectValue,titleValue,summaryValue,date,time,nameValue,genreValue)
         else:
            result = []
            for row in values:
               subjectValue = strip(row[0])
               titleValue = literal(row[1])
               summaryValue = literal(row[2]) if row[2] is not None else None
               date,time = strip(row[3]).split('T')
               nameValue = strip(row[4])
               genreValue = strip(row[5])
               result.append((subjectValue,titleValue,summaryValue,date,time,nameValue,genreValue))
            return result
      else:
         raise IOError('Cannot post data to uri <{}>, status={}'.format(self.service,req.status_code))

   def entityByOrder(self,value,entity = None,order = None,title = None,summary = None,resource = None, criteria = None, name=None, genre=None):
      return self.entityByValue(value,self.facet('order',order),entity=entity,order=order,title=title,summary=summary,resource=resource,criteria=criteria,name=name,genre=genre)

   def entityByValue(self,value,facet,entity = None,order = None,title = None,summary = None,resource = None, criteria = None, name=None, genre=None):
      entityType = self.facet('type',entity)
      orderFacet = self.facet('order',order)
      titleFacet = self.facet('title',title)
      summaryFacet = self.facet('summary',summary)
      nameFacet = self.facet('name',name)
      genreFacet = self.facet('genre',genre)
      expr = '?s {0} ?ordering; {1} ?title; {3} {4}; {5} ?name; {6} ?genre . optional {{ ?s {2} ?summary . }}'.format(orderFacet,titleFacet,summaryFacet,facet,facet.toLiteral(value),nameFacet,genreFacet)
      if criteria is not None:
         expr = expr + criteriaConditions(self,criteria)
      q = SPARQL() \
            .start(self.prefixes) \
            .select(['s','title','summary','ordering','name','genre']) \
            .fromGraphs(self.graphs) \
            .where(expr)
      if self.logger.isEnabledFor(logging.DEBUG):
         self.logger.debug(str(q))
      params = self.mergeParameters({'limit':1,'query':str(q)})

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         values = data['values']
         if len(values)==0:
            return None
         subject = strip(values[0][0])
         title = literal(values[0][1])
         summary = literal(values[0][2]) if values[0][2] is not None else None
         dateTime = strip(values[0][3])
         date,time = dateTime.split('T') # Need to check that is xsd:dateTime
         nameValue = strip(values[0][4])
         genreValue = strip(values[0][5])
         return (subject,title,summary,date,time,nameValue,genreValue)
      else:
         raise IOError('Cannot post data to uri <{}>, status={}'.format(self.service,req.status_code))

   def getCategoryCount(self,entity = None,category = None):
      entityType = self.facet('type',entity)
      categoryFacet = self.facet('category',category)
      expr = '?s rdf:type {0}; {1} ?category'.format(entityType,categoryFacet)
      q = SPARQL() \
            .start(self.prefixes) \
            .select(['category','(count(?category) as ?count)']) \
            .fromGraphs(self.graphs) \
            .where(expr) \
            .groupBy('?category') \
            .orderBy('desc(?count)')
      if self.logger.isEnabledFor(logging.DEBUG):
         self.logger.debug(str(q))
      params = self.mergeParameters({'limit':100,'query':str(q)})

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         keywords = {}
         for keyword in data['values']:
            value,type = keyword[1].split('^^')
            keywords[strip(keyword[0])] = int(strip(value))
         return keywords
      else:
         raise IOError('Cannot post data to uri <{}>, status={}'.format(self.service,req.status_code))

   def getEntityCategories(self,subject,entity = None,category = None):
      entityType = self.facet('type',entity)
      categoryFacet = self.facet('category',category)
      expr = '<{0}> rdf:type {1}; {2} ?category'.format(subject,entityType,categoryFacet)
      q = SPARQL() \
            .start(self.prefixes) \
            .select(['category']) \
            .fromGraphs(self.graphs) \
            .where(expr)
      if self.logger.isEnabledFor(logging.DEBUG):
         self.logger.debug(str(q))
      params = self.mergeParameters({'limit':100,'query':str(q)})

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         keywords = []
         for keyword in data['values']:
            keywords.append(strip(keyword[0]))
         return keywords
      else:
         raise IOError('Cannot post data to uri <{}>, status={}'.format(self.service,req.status_code))

   def getEntitiesByCategory(self,value,limit = 100,entity = None,category = None,title = None,summary = None,order = None,resource = None, name=None, genre=None):
      entityType = self.facet('type',entity)
      categoryFacet = self.facet('category',category)
      titleFacet = self.facet('title',title)
      summaryFacet = self.facet('summary',summary)
      orderFacet = self.facet('order',order)
      nameFacet = self.facet('name',name)
      genreFacet = self.facet('genre',genre)
      expr = '?s rdf:type {0}; {1} ?title; {3} ?date; {4} {5}; {6} ?name; {7} ?genre; . optional {{ ?s {2} ?summary; }}'.format(entityType,titleFacet,summaryFacet,orderFacet,categoryFacet,categoryFacet.toLiteral(value),nameFacet,genreFacet)
      q = SPARQL() \
            .start(self.prefixes) \
            .select(['s','title','summary','date','name','genre']) \
            .fromGraphs(self.graphs) \
            .where(expr)
      if self.logger.isEnabledFor(logging.DEBUG):
         self.logger.debug(str(q))
      params = self.mergeParameters({'limit':limit,'query':str(q)})

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         result = []
         for row in data['values']:
            subjectValue = strip(row[0])
            titleValue = literal(row[1])
            summaryValue = literal(row[2]) if row[2] is not None else None
            date,time = strip(row[3]).split('T')
            nameValue = strip(row[4])
            genreValue = strip(row[5])
            result.append((subjectValue,titleValue,summaryValue,date,time,nameValue,genreValue))
         return result
      else:
         raise IOError('Cannot post data to uri <{}>, status={}'.format(self.service,req.status_code))

   def getEntityResource(self,subject,singleton = False,resource=None,contentUrl=None,fileFormat=None,criteria=None):
      resourceFacet = self.facet('resource',resource)
      if resourceFacet.type=='schema:MediaObject':
         contentUrlFacet = self.facet('contentUrl',contentUrl)
         fileFormatFacet = self.facet('fileFormat',fileFormat)
         expr = '<{0}> {1} ?r . ?r rdf:type ?type; {2} ?url; {3} ?format .'.format(subject,resourceFacet,contentUrlFacet,fileFormatFacet)
         if criteria is not None:
            expr = expr + criteriaConditions(self,criteria,subjectVar='r')
         q = SPARQL() \
               .start(self.prefixes) \
               .select(['url','format','type']) \
               .fromGraphs(self.graphs) \
               .where(expr)
         if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(str(q))
         params = self.mergeParameters({'query':str(q)})
         req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

         if (req.status_code>=200 or req.status_code<300):
            data = json.loads(req.text)
            values = data['values']
            if len(values)==0:
               return None
            elif len(values)==1 and not singleton:
               row = values[0]
               return (strip(row[0]),strip(row[1]),strip(row[2]))
            else:
               result = []
               for row in values:
                  result.append((strip(row[0]),strip(row[1]),strip(row[2])))
               return result
         else:
            raise IOError('Cannot get data from uri <{}>, status={}'.format(self.service,req.status_code))
      elif resourceFacet.type=='xsd:anyURI':
         expr = '<{0}> {1} ?url.'.format(subject,resourceFacet)
         if criteria is not None:
            expr = expr + criteriaConditions(self,criteria,subjectVar='r')
         q = SPARQL() \
               .start(self.prefixes) \
               .select(['url']) \
               .fromGraphs(self.graphs) \
               .where(expr)
         if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(str(q))
         params = self.mergeParameters({'query':str(q)})
         req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)
         if (req.status_code>=200 or req.status_code<300):
            data = json.loads(req.text)
            values = data['values']
            if len(values)==0:
               return None
            elif len(values)==1 and not singleton:
               row = values[0]
               return (strip(row[0]),None,None)
            else:
               result = []
               for row in values:
                  result.append((strip(row[0]),None,None))
               return result
         else:
            raise IOError('Cannot get data from uri <{}>, status={}'.format(self.service,req.status_code))
      else:
         raise IOError('Cannot determine resource facet query, type {}'.format(resourceFacet.type))
