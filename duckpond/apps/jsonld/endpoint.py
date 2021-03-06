from flask import has_request_context, has_app_context, current_app, request, g
import requests
import json
import urllib
from pyld import jsonld
from duckpond.data import SPARQL,var,expr,in_expr,tuple_expr,graph_expr
import re

class RESTIOError(IOError):
   def __init__(self,msg,url,status,text):
      super().__init__(msg)
      self.url = url;
      self.status = status
      self.text = text

def uri_parameter(uris):
   return list(map(lambda x: '<' + str(x) + '>',uris))

def unpack_value(value):
   if (value[0]=='<' and value[-1]=='>') or (value[0]=='"' and value[-1]=='"'):
      return value[1:-1]
   else:
      return value

def from_json(quads):
   subjects = {}
   for quad in quads:
      target = subjects.get(quad[0])
      if target is None:
         target = {'@id':unpack_value(quad[0])}
         subjects[quad[0]] = target
      predicate = unpack_value(quad[1])
      value = target.get(predicate)
      new_value = unpack_value(quad[2])
      if value is None:
         target[predicate] = new_value
      elif type(value)==list:
         list.append(new_value)
      else:
         target[predicate] = [value,new_value]
   ld = list(subjects.values())
   if len(ld)==1:
      ld = ld[0]
   return ld

def subjectClause(out,subjects):
   out.write('?s IN (')
   for index,s in enumerate(subjects):
      if index>0:
         out.write(',')
      out.write(uri_parameter(subject))
   out.write(')')


class SPARQLConnection:
   def __init__(self,url,username=None,password=None,context={}):
      self.url = url
      if self.url[-1]=='/':
         self.url = self.url[0:-1]
      self.username = username
      self.password = password
      self.context = context

   def get(self,graphs=[],subjects=[],limit=None):

      query = SPARQL().construct(['s','p','o'])

      tuples = tuple_expr('s','p','o')
      if len(subjects)>0:
         tuples.filter(in_expr(var('s'),*subjects))

      if len(graphs)==0 :
         query.where(tuples)
      else:
         query.where(*list(map(lambda g:graph_expr(g,tuples),graphs)))

      #print(query)

      params = {}
      params = {'query':str(query)}
      if limit is not None:
         params['limit'] = limit
      uri = self.url
      req = requests.post(uri,params=params,headers={'accept':'application/json','content-type':'application/x-www-form-urlencoded; charset=utf-8'},auth=self.get_authentication())

      #print(req.headers)

      if req.status_code>=200 and req.status_code<300:
         data = json.loads(req.text)
         #print(data)
         data = from_json(data)
         #print(data)
         return data
      else:
         raise RESTIOError('Cannot retrieve graph and subjects, status={}'.format(req.status_code),uri,req.status_code,req.text)

   def query(self,q,limit=None):
      params = {'query':str(q)}
      if limit is not None:
         params['limit'] = limit

      isSelect = re.search('SELECT(\s+\?\w+)+',q,re.IGNORECASE)

      uri = self.url
      req = requests.post(uri,params=params,headers={'accept':'application/json','content-type':'application/x-www-form-urlencoded; charset=utf-8'},auth=self.get_authentication())

      #print(req.headers)

      if req.status_code>=200 and req.status_code<300:
         data = json.loads(req.text)
         if not isSelect:
            data = from_json(data)
         return data
      else:
         raise RESTIOError('Cannot query repository:\n{}\n{}\nstatus={}'.format(q,req.text,req.status_code),uri,req.status_code,req.text)

   def delete(self,graphs=[],subjects=[]):
      tuples = tuple_expr('s','p','o')
      if len(subjects)>0:
         tuples.filter(in_expr(var('s'),*subjects))
      if len(graphs)==0 :
         query.delete(tuples)
      else:
         query.delete(*list(map(lambda g:graph_expr(g,tuples),graphs)))

      params = {}
      params = {'query':str(query)}
      uri = self.url
      req = requests.post(uri,params=params,headers={'accept':'application/json','content-type':'application/x-www-form-urlencoded; charset=utf-8'},auth=self.get_authentication())

      if (req.status_code<200 or req.status_code>=300):
         raise RESTIOError('Cannot delete graphs {}, status={}'.format(graphs,req.status_code),uri,req.status_code,req.text)

   def update(self,data,graph=None,subjects=[]):

      tuples = tuple_expr('s','p','o')
      if len(subjects)>0:
         tuples.filter(in_expr(var('s'),*subjects))
      if graph is None:
         query.delete(tuples)
      else:
         query.delete(graph_expr(graph,tuples))

      content = jsonld.normalize(data, {'algorithm': 'URDNA2015', 'format': 'application/nquads'}).encode('utf-8')
      query.insert(graph_expr(graph,content) if graph is not None else content)

      params = {}
      params = {'query':str(query)}
      uri = self.url
      req = requests.post(uri,params=params,headers={'accept':'application/json','content-type':'application/x-www-form-urlencoded; charset=utf-8'},auth=self.get_authentication())

      if (req.status_code<200 or req.status_code>=300):
         raise RESTIOError('Cannot update graph {}, status={}'.format(graph,req.status_code),uri,req.status_code,req.text)

   def append(self,data,graph=None):

      content = jsonld.normalize(data, {'algorithm': 'URDNA2015', 'format': 'application/nquads'}).encode('utf-8')
      query.insert(graph_expr(graph,content) if graph is not None else content)

      params = {}
      params = {'query':str(query)}
      uri = self.url
      req = requests.post(uri,params=params,headers={'accept':'application/json','content-type':'application/x-www-form-urlencoded; charset=utf-8'},auth=self.get_authentication())

      if (req.status_code<200 or req.status_code>=300):
         raise RESTIOError('Cannot append to graph {}, status={}'.format(graph,req.status_code),uri,req.status_code,req.text)

   def get_authentication(self):
      if self.username is None:
         if has_request_context() and request.authorization is not None:
            return (request.authorization.username, request.authorization.password)
         else:
            return None
      else:
         return (self.username, self.password)

def make_connection(url,username=None,password=None,context=None):
   return SPARQLConnection(url,username,password,context)

def get_connection():
   if has_app_context():
      connection = getattr(g,'_jsonld_service',None)
      if connection is None:
         service_def = current_app.config.get('SPARQL_ENDPOINT')
         context = current_app.config.get('LD_CONTEXT')

         _make_connection = getattr(g,'_jsonld_make_connection',None)
         if _make_connection is None:
            _make_connection = make_connection
         connection = g._jsonld_service = _make_connection(service_def.get('url'),username=service_def.get('username'),password=service_def.get('password'),context=context)
      return connection
   else:
      raise ValueError('No connection can be created')

def get_ld(graphs=[],subjects=[],connection=None):
   if connection is None:
      connection = get_connection()

   ld = connection.get(graphs,subjects)
   return jsonld.compact(ld,connection.context)

def query_ld(q,limit=None,connection=None):
   if connection is None:
      connection = get_connection()

   ld = connection.query(q,limit=limit)
   return ld if ld.get('names') is not None and ld.get('values') is not None else jsonld.compact(ld,connection.context)

def delete_ld(graphs=[],subjects=[],connection=None):
   if connection is None:
      connection = get_connection()

   connection.delete(graphs,subjects)

def update_ld(data,graph=None,subjects=[],connection=None):
   if connection is None:
      connection = get_connection()

   return connection.replace(data,graph,subjects)

def append_ld(data,graph=None,connection=None):
   if connection is None:
      connection = get_connection()

   return connection.append(data,graph)
