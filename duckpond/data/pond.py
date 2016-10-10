import requests
import json,io
from enum import Enum
from .util import relative
import urllib
from .sparql import SPARQL

def strip(value):
   if value is None:
      return value
   elif value[0]=='"':
      value = value[1:-1]
      if value[0]=='<' and value[-1]=='>':
         return value[1:-1]
      else:
         return value
   elif value[0]=='<':
      return value[1:-1]
   else:
      return value


class Pond:

   class AuthMethod(Enum):
      basic = 1
      digest = 2

   class ResourceType(Enum):
      uri = 1
      stream = 2
      local = 3

   def __init__(self,service,cache=None,facets=None,graphs=None):
      self.service = service
      self.cache = cache
      self.serviceAuth = self.authenticate("anonymous")
      self.resourceAuth = None
      self.prefixes = { 'schema' : 'http://schema.org/'}
      self.graphs = []
      if graphs is not None:
         for graph in graphs:
            self.graphs.append(graph)
      self.facets = { 'type' : 'schema:BlogPosting',
           'order' : 'schema:datePublished',
           'title' : 'schema:headline',
           'summary' : 'schema:description',
           'resource' : 'schema:isBasedOnUrl',
           'category' : 'schema:keywords'}
      if facets is not None:
         for key in facets.keys():
            self.facets[key] = facet[key]

   def getProlog(self):
      glob = io.StringIO()
      for key in self.prefixes:
         glob.write("prefix {}: <{}>".format(key,self.prefixes[key]))
      return glob.getvalue()

   def setProxyCache(self,proxy,base):
      self.cache = { 'proxy': proxy, 'base':base }

   def authenticate(self,user,password="",method=AuthMethod.basic):
      if (method is Pond.AuthMethod.basic):
         self.auth = requests.auth.HTTPBasicAuth(user, password)
      elif (method is Pond.AuthMethod.digest):
         self.auth = requests.auth.HTTPDigestAuth(user, password)
      else:
         raise Exception("Unsupported authentication method")

   def defaultParameters(self):
      params = {}
      return params

   def mergeParameters(self,requestParameters):
      params = self.defaultParameters()
      for param in requestParameters.keys():
         params[param] = requestParameters[param]
      return params

   def getGraphs(self):
      named = ""
      for graph in self.graphs:
         named = named + "from named <" + graph +"> "
      return named

   def facet(self,name,value = None):
      return value if value is not None else self.facets[name]

   def currentEntity(self,entity = None,order = None,title = None, summary = None, resource = None):

      entityType = self.facet('type',entity)
      orderFacet = self.facet('order',order)
      titleFacet = self.facet('title',title)
      summaryFacet = self.facet('summary',summary)
      resourceFacet = self.facet('resource',resource)

      expr = '?s rdf:type {0}; {1} ?ordering; {2} ?title; {4} ?basedOnUrl . optional {{ ?s {3} ?summary . }}'.format(entityType,orderFacet,titleFacet,summaryFacet,resourceFacet)
      q = SPARQL() \
            .start(self.prefixes) \
            .select(["s","title","summary","ordering","basedOnUrl"]) \
            .fromGraphs(self.graphs) \
            .where(expr) \
            .orderBy("desc(?ordering)")
      #print(q)
      params = self.mergeParameters({'limit':1,'query':str(q)})

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         #print(req.text)
         data = json.loads(req.text)
         if len(data['values']) == 0:
            return (None,None,None,None,None,None)
         subject = strip(data['values'][0][0])
         title = strip(data['values'][0][1])
         summary = strip(data['values'][0][2])
         dateTime = strip(data['values'][0][3])
         basedOnUrl = strip(data['values'][0][4])
         date,time = dateTime.split('T') # Need to check that is xsd:dateTime
         #{'uri':relative(strip(data['values'][1][0])),'title':strip(data['values'][1][1]),'summary':strip(data['values'][1][2])} if len(data['values'])>1 else None
         return (subject,title,summary,date,time,basedOnUrl)
      else:
         raise IOError('Cannot post data to uri <{}>, status={}'.format(self.service,req.status_code))

   def proxyURL(self,resource):
      uri = resource
      if not self.cache==None and 'proxy' in self.cache and 'base' in self.cache:
         base = self.cache['base']
         relative = resource[resource.index(base) + len(base):]
         uri = self.cache['proxy'] + relative
      return uri

   def getResourceText(self,resource):

      uri = self.proxyURL(resource)

      if self.cache==None or uri[0:5]=='http:' or uri[0:6]=='https:':
         req = requests.get(uri,auth=self.resourceAuth)
         if (req.status_code == 200):
            return req.text
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
         req = requests.get(uri, stream = True,auth=self.resourceAuth)
         return (Pond.ResourceType.stream,req.iter_content(),req.headers['content-type'])
      elif uri[0:7]=='file://':
         return (Pond.ResourceType.local, uri[7:],None)
      else:
         return (Pond.ResourceType.local, uri,None)

   def relatedEntityByOrder(self,value,previous = True,entity = None,order = None,title = None,summary = None):
      entityType = self.facet('type',entity)
      orderFacet = self.facet('order',order)
      titleFacet = self.facet('title',title)
      summaryFacet = self.facet('summary',summary)
      expr = '?s rdf:type {0}; {1} ?ordering; {2} ?title; . optional {{ ?s {3} ?summary . }}'.format(entityType,orderFacet,titleFacet,summaryFacet) \
             + ' FILTER( ?ordering ' + ('>' if previous else '<') + ' "' + value + '"' + ' )'
      q = SPARQL() \
            .start(self.prefixes) \
            .select(["s","title","summary","ordering","basedOnUrl"]) \
            .fromGraphs(self.graphs) \
            .where(expr ) \
            .orderBy("desc(?ordering)")
      #print(q)
      params = self.mergeParameters({'limit':1,'query':str(q)})

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         values = data['values']
         return {'uri':relative(strip(values[0][0])),'title':strip(values[0][1]),'summary':strip(values[0][2]) } if len(values)>0 else None
      else:
         raise IOError('Cannot post data to uri <{}>, status={}'.format(self.service,req.status_code))

   def entityByOrder(self,ordering,entity = None,order = None,title = None,summary = None,resource = None):
      entityType = self.facet('type',entity)
      orderFacet = self.facet('order',order)
      titleFacet = self.facet('title',title)
      summaryFacet = self.facet('summary',summary)
      resourceFacet = self.facet('resource',resource)
      expr = '?s rdf:type {0}; {1} "{2}"; {3} ?title; {5} ?basedOnUrl . optional {{ ?s {4} ?summary . }}'.format(entityType,orderFacet,ordering,titleFacet,summaryFacet,resourceFacet)
      q = SPARQL() \
            .start(self.prefixes) \
            .select(["s","title","summary","basedOnUrl"]) \
            .fromGraphs(self.graphs) \
            .where(expr)
      #print(q)
      params = self.mergeParameters({'limit':1,'query':str(q)})

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         values = data['values']
         subject = strip(values[0][0])
         title = strip(values[0][1])
         summary = strip(values[0][2])
         basedOnUrl = strip(values[0][3])
         date,time = ordering.split('T') # Need to check that is xsd:dateTime
         return (subject,title,summary,date,time,basedOnUrl)
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
      #print(q)
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

   def getEntitiesByCategory(self,value,limit = 100,entity = None,category = None,title = None,summary = None,order = None):
      entityType = self.facet('type',entity)
      categoryFacet = self.facet('category',category)
      titleFacet = self.facet('title',title)
      summaryFacet = self.facet('summary',summary)
      orderFacet = self.facet('order',order)
      expr = '?s rdf:type {0}; {1} ?title; {3} ?date; {4} "{5}" . optional {{ ?s {2} ?summary; }}'.format(entityType,titleFacet,summaryFacet,orderFacet,categoryFacet,value)
      q = SPARQL() \
            .start(self.prefixes) \
            .select(['s','date','title','summary']) \
            .fromGraphs(self.graphs) \
            .where(expr)
      params = self.mergeParameters({'limit':limit,'query':str(q)})

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         entries = []
         for entry in data['values']:
            entries.append({'subject': strip(entry[0]), 'uri': relative(strip(entry[0])), 'datePublished' : strip(entry[1]), 'title' : strip(entry[2]), 'summary' : strip(entry[3])})
         return entries
      else:
         raise IOError('Cannot post data to uri <{}>, status={}'.format(self.service,req.status_code))
