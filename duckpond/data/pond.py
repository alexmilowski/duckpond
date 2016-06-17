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

   def setProxyCache(self,proxy,base):
      this.cache = { 'proxy': proxy, 'base':base }

   def authenticate(self,user,password="",method=AuthMethod.basic):
      if (method is Pond.AuthMethod.basic):
         self.auth = requests.auth.HTTPBasicAuth(user, password)
      elif (method is Pond.AuthMethod.digest):
         self.auth = requests.auth.HTTPDigestAuth(user, password)
      else:
         raise Exception("Unsupported authentication method")

   def currentEntry(self):
      query = """
prefix schema: <http://schema.org/>
select ?s ?headline ?date ?basedOnUrl where { ?s rdf:type schema:BlogPosting; schema:datePublished ?date; schema:headline ?headline; schema:isBasedOnUrl ?basedOnUrl } order by desc(?date)
"""   
      params = {'limit':2,'query':query}
   
      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         subject = data['values'][0][0][1:-1]
         title = data['values'][0][1][1:-1]
         dateTime = data['values'][0][2][1:-1]
         basedOnUrl = data['values'][0][3][1:-1]
         date,time = dateTime.split('T')
         return (subject,title,date,time,basedOnUrl,{'uri':relative(data['values'][1][0][1:-1]),'title':data['values'][1][1][1:-1]} if len(data['values'])>1 else None)
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
   
   def relatedEntry(self,dateTime,previous):
      query = """
prefix schema: <http://schema.org/>
select ?s ?headline ?date 
where { 
   ?s rdf:type schema:BlogPosting; schema:datePublished ?date; schema:headline ?headline .
   FILTER( ?date """ + ('>' if previous else '<') + ' "' + dateTime + '"' + """ )
} 
order by """ + ('?date' if previous else 'desc(?date)')
      params = {'limit':1,'query':query}

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         return {'uri':relative(data['values'][0][0][1:-1]),'title':data['values'][0][1][1:-1]} if len(data['values'])>0 else None
      else:
         raise IOError('Cannot post data to uri <{}>, status={}'.format(self.service,req.status_code))

   def entryByDateTime(self,dateTime):
      query = """
prefix schema: <http://schema.org/>
select ?s ?headline ?isBasedOnUrl
where { 
   ?s rdf:type schema:BlogPosting; schema:datePublished """ + '"' + dateTime + '"' + """; schema:headline ?headline ; schema:isBasedOnUrl ?isBasedOnUrl.
} 
"""
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

   def getKeywordCount(self):
      query = """
prefix schema: <http://schema.org/>
select ?keyword (count(?keyword) as ?count)
where { 
     ?s rdf:type schema:BlogPosting; schema:keywords ?keyword 
}
group by ?keyword
order by desc(?count)
"""   
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

   def getEntryKeywords(self,subject):
      query = """
prefix schema: <http://schema.org/>
select ?keyword 
where { 
   <""" + subject +"""> rdf:type schema:BlogPosting; schema:keywords ?keyword 
}
"""   
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

   def getEntriesByKeyword(self,keyword):
      query = """
prefix schema: <http://schema.org/>
select ?s ?date ?headline 
where { 
   ?s rdf:type schema:BlogPosting; schema:headline ?headline; schema:datePublished ?date; schema:keywords """ + '"' + keyword + '"' """ 
}
"""   
      params = {'limit':100,'query':query}

      req = requests.get(self.service,params=params,headers={'accept':'application/json'},auth=self.serviceAuth)

      if (req.status_code>=200 or req.status_code<300):
         data = json.loads(req.text)
         entries = []
         for entry in data['values']:
            entries.append({'subject': entry[0][1:-1], 'uri': relative(entry[0][1:-1]), 'datePublished' : entry[1][1:-1], 'title' : entry[2][1:-1]})
         return entries
      else:
         raise IOError('Cannot post data to uri <{}>, status={}'.format(self.service,req.status_code))

