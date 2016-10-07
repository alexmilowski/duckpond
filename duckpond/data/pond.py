import requests
import json
from enum import Enum
from .util import relative

class Pond:

   class AuthMethod(Enum):
      basic = 1
      digest = 2

   class ResourceType(Enum):
      uri = 1
      stream = 2
      local = 3

   def __init__(self,service,cache=None):
      self.service = service
      self.cache = cache
      self.serviceAuth = self.authenticate("anonymous")
      self.resourceAuth = None
      self.prefixes = { 'schema' : 'http://schema.org'}
      self.facets =
         { 'type' : 'schema:BlogPosting',
           'order' : 'schema:datePublished',
           'summary' : 'schema:headline',
           'resource' : 'schema:isBasedOnUrl',
           'category' : 'schema:keywords'}

   def getProlog(self):
      glob = io.StringIO()
      for key in self.prefixes:
         glob.write("prefix {}: <{}>".format(key,self.prefixes[key]))
      return glob.getvalue()

   def setProxyCache(self,proxy,base):
      this.cache = { 'proxy': proxy, 'base':base }

   def authenticate(self,user,password="",method=AuthMethod.basic):
      if (method is Pond.AuthMethod.basic):
         self.auth = requests.auth.HTTPBasicAuth(user, password)
      elif (method is Pond.AuthMethod.digest):
         self.auth = requests.auth.HTTPDigestAuth(user, password)
      else:
         raise Exception("Unsupported authentication method")

   def facet(name,value = None):
      return value if value is not None else self.facets[name]

   def currentEntity(self,entityType = None,order = None,summary = None, resource = None):

      entityType = self.facet('type',entityType)
      orderFacet = self.facet('order',order)
      summaryFacet = self.facet('summary',summary)
      resourceFacet = self.facet('resource',resource)

      query = self.getProlog() + """
select ?s ?summary ?ordering ?basedOnUrl where { ?s rdf:type {1}; {2} ?ordering; {3} ?summary; {4} ?basedOnUrl } order by desc(?date)
""".format(entityType,orderFacet,summaryFacet,resourceFacet)
      params = {'limit':2,'query':query}

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         subject = data['values'][0][0][1:-1]
         summary = data['values'][0][1][1:-1]
         dateTime = data['values'][0][2][1:-1]
         basedOnUrl = data['values'][0][3][1:-1]
         date,time = dateTime.split('T') # Need to check that is xsd:dateTime
         return (subject,summary,date,time,basedOnUrl,{'uri':relative(data['values'][1][0][1:-1]),'summary':data['values'][1][1][1:-1]} if len(data['values'])>1 else None)
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
      if cache==None or uri[0:5]=='http:' or uri[0:6]=='https:':
         req = requests.get(uri, stream = True,auth=self.resourceAuth)
         return (Pond.ResourceType.stream,req.iter_content(),req.headers['content-type'])
      elif uri[0:7]=='file://':
         return (Pond.ResourceType.local, uri[7:],None)

   def relatedEntityByOrder(self,orderValue,previous = True,entityType = None,order = None,summary = None):
      entityType = self.facet('type',entityType)
      orderFacet = self.facet('order',order)
      summaryFacet = self.facet('summary',summary)
      query = self.getProlog() + """
select ?s ?summary ?ordering
where {
   ?s rdf:type {1}; {2} ?ordering; {3} ?summary .
   FILTER( ?ordering """ + ('>' if previous else '<') + ' "' + dateTime + '"' + """ )
}
order by """.format(entityType,orderFacet,summaryFacet) + ('?ordering' if previous else 'desc(?ordering)')
      params = {'limit':1,'query':query}

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         return {'uri':relative(data['values'][0][0][1:-1]),'title':data['values'][0][1][1:-1]} if len(data['values'])>0 else None
      else:
         raise IOError('Cannot post data to uri <{}>, status={}'.format(self.service,req.status_code))

   def entityByOrder(self,orderValue,entityType = None,order = None,summary = None,resource = None):
      entityType = self.facet('type',entityType)
      orderFacet = self.facet('order',order)
      summaryFacet = self.facet('summary',summary)
      resourceFacet = self.facet('resource',resource)
      query = self.getProlog() + """
select ?s ?headline ?isBasedOnUrl
where {
   ?s rdf:type {1}; {2} """ + '"' + orderValue + '"' + """; {3} ?headline ; {4} ?isBasedOnUrl.
}
""".format(entityType,orderFacet,summaryFacet,resourceFacet)
      params = {'limit':1,'query':query}

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         subject = data['values'][0][0][1:-1]
         headline = data['values'][0][1][1:-1]
         basedOn = data['values'][0][2][1:-1]
         return (subject,headline,basedOn) if len(data['values'])>0 else (None,None,None)
      else:
         raise IOError('Cannot post data to uri <{}>, status={}'.format(self.service,req.status_code))

   def getCategoryCount(self,entity = None,category = None):
      entityType = self.facet('type',entityType)
      categoryFacet = self.facet('category',category)
      query = self.getProlog() + """
select ?category (count(?category) as ?count)
where {
     ?s rdf:type {1}; {2} ?category
}
group by ?category
order by desc(?count)
""".format(entityType,categoryFacet)
      params = {'limit':100,'query':query}

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         keywords = {}
         for keyword in data['values']:
            value,type = keyword[1].split('^^')
            keywords[keyword[0][1:-1]] = int(value[1:-1])
         return keywords
      else:
         raise IOError('Cannot post data to uri <{}>, status={}'.format(self.service,req.status_code))

   def getEntityCategories(self,subject,entity = None,category = None):
      entityType = self.facet('type',entityType)
      categoryFacet = self.facet('category',category)
      query = """
prefix schema: <http://schema.org/>
select ?category
where {
   <""" + subject +"""> rdf:type {1}; {2} ?category
}
""".format(entityType,categoryFacet)
      params = {'limit':100,'query':query}

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         keywords = []
         for keyword in data['values']:
            keywords.append(keyword[0][1:-1])
         return keywords
      else:
         raise IOError('Cannot post data to uri <{}>, status={}'.format(self.service,req.status_code))

   def getEntitiesByCategory(self,category,limit = 100,entity = None,category = None,order = None,summary = None):
      entityType = self.facet('type',entityType)
      categoryFacet = self.facet('category',category)
      summaryFacet = self.facet('summary',summary)
      orderFacet = self.facet('order',order)
      query = """
prefix schema: <http://schema.org/>
select ?s ?date ?headline
where {
   ?s rdf:type {1}; {2} ?headline; {3} ?date; {4} """ + '"' + category + '"' """
}
""".format(entityType,summaryFacet,orderFacet,categoryFacet)
      params = {'limit':limit,'query':query}

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         entries = []
         for entry in data['values']:
            entries.append({'subject': entry[0][1:-1], 'uri': relative(entry[0][1:-1]), 'datePublished' : entry[1][1:-1], 'title' : entry[2][1:-1]})
         return entries
      else:
         raise IOError('Cannot post data to uri <{}>, status={}'.format(self.service,req.status_code))
