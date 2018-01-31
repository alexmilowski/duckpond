from flask import Blueprint, request, abort, make_response, jsonify, current_app
import logging
import requests
import json
from duckpond.apps.jsonld.endpoint import get_ld, query_ld, update_ld, delete_ld, append_ld

prefix = 'duckpond_service_jsonld'
data = Blueprint(prefix+'_data',__name__,template_folder='templates')

logger = logging.getLogger('webapp')

def content_type():
   contentType = request.headers.get('Content-Type')
   if contentType is None:
      return ('application/octet-stream',None)
   parts = contentType.split(';')
   charset = 'UTF-8'
   for part in parts[1:]:
      part = part.strip()
      param = part.split('=')
      if param[0].strip()=='charset':
         charset = param[1].strip()
   return (parts[0],charset)

def jsonld_response(data):
   if data is None:
      data = {}
   if type(data)==dict or type(data)==list:
      data = json.dumps(data)
   response = make_response(data)
   response.headers['Content-Type'] = "application/ld+json; charset=utf-8"
   return response

def json_response(data):
   if data is None:
      data = {}
   if type(data)==dict or type(data)==list:
      data = json.dumps(data)
   response = make_response(data)
   response.headers['Content-Type'] = "application/json; charset=utf-8"
   return response

@data.errorhandler(400)
def api_error_400(error):
   response = jsonify({'message': error.description,'status' : 400})
   response.status_code = 400
   response.headers['Content-Type'] = "application/json; charset=utf-8"
   return response

def by_graph(graphs,subjects):
   if request.method=='GET':
      ld = get_ld(graphs,subjects)
      return jsonld_response(ld)
   elif request.method=='DELETE':
      delete_ld(graphs,subject)
   else:
      request_type = content_type()
      if request_type[0]=='application/ld+json':
         if graphs is not None and len(graphs)>1:
            abort(400,'Only one graph may be specified on update/append.')
         json = request.get_json(force=True)
         ld = jsonld.compact(json,current_app.config.get('LD_CONTEXT'))
         if request.method=='POST':
            append_ld(ld,graphs=graphs[0] if graphs is not None and len(graphs)>0 else None,subjects=subjects)
         else:
            update_ld(ld,graph=graphs[0] if graphs is not None and len(graphs)>0 else None,subjects=subjects)
         return ('',201)
      elif request_type[0]=='application/sparql-update':
         if request.method=='POST':
            abort(400,'Invalid method POST with SPARQL update.')
         if len(graphs)>0:
            abort(400,'The graph parameter may not be specified via update - incorporate into the SPARQL update statement.')
         if len(subjects)>0:
            abort(400,'The subject parameter may not be specified via update - incorporate into the SPARQL update statement.')

         ld = query_ld(request.data.decode(encoding=request_type[1]),limit=request.args.get('limit'))
         return jsonld_response(ld)
      elif request_type[0]=='application/sparql-query':
         if request.method=='PUT':
            abort(400,'Invalid method PUT with SPARQL query.')
         if len(graphs)>0:
            abort(400,'The graph parameter may not be specified via query - incorporate into the SPARQL update statement.')
         if len(subjects)>0:
            abort(400,'The subject parameter may not be specified via query - incorporate into the SPARQL update statement.')
         ld = query_ld(request.data.decode(encoding=request_type[1]),limit=request.args.get('limit'))
         return json_response(ld) if ld.get('names') is not None and ld.get('values') is not None else jsonld_response(ld)
      else:
         abort(400,'Unrecognized media type: '+request_type[0])

@data.route('/',methods=['GET','POST','PUT','DELETE'])
def any_graph():
   subjects = request.args.getlist('subject')
   graphs = request.args.getlist('graph')
   return by_graph(graphs,subjects)

@data.route('/<graph>/',methods=['GET','POST','PUT','DELETE'])
def graph_path(graph):
   subjects = request.args.getlist('subject')
   return by_graph([graph],subjects)
