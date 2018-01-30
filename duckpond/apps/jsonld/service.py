from flask import Blueprint, request, abort, make_response, jsonify, current_app
import logging
import requests
import json
from pyld import jsonld
from duckpond.apps.jsonld.endpoint import get, query, update_graph, delete_graph, append_graph

prefix = 'duckpond_service_jsonld'
data = Blueprint(prefix+'_data',__name__,template_folder='templates')

logger = logging.getLogger('webapp')

def content_type():
   contentType = request.headers.get('Content-Type')
   if contentType is None:
      return ('application/octet-stream',None)
   parts = contentType.split(';')
   charset = None
   for part in parts[1:]:
      part = part.strip()
      param = part.split('=')
      if param[0].strip()=='charset':
         charset = param[1].strip()
   return (contentType,charset)

def jsonld_response(data):
   if data is None:
      data = {}
   if type(data)==dict or type(data)==list:
      data = json.dumps(data)
   response = make_response(data)
   response.headers['Content-Type'] = "application/ld+json; charset=utf-8"
   return response

@data.errorhandler(400)
def api_error_400(error):
   response = jsonify({'message': error.description,'status' : 400})
   response.status_code = 400
   response.headers['Content-Type'] = "application/json; charset=utf-8"
   return response

@data.route('/',methods=['GET','POST','PUT'])
def retrieve():
   if request.method=='GET':
      subjects = request.args.getlist('subject')
      graphs = request.args.getlist('graph')
      ld = get(graphs,subjects)
      return jsonld_response(jsonld.compact(ld,current_app.config.get('LD_CONTEXT')))
   else:
      request_type = content_type()
      if request_type[0]=='application/ld+json':
         graphs = request.args.getlist('graph')
         if graphs is not None and len(graphs)>1:
            abort(400,'Only one graph may be specified on update.')
         json = request.get_json(force=True)
         ld = jsonld.compact(json,current_app.config.get('LD_CONTEXT'))
         if request.method=='POST':
            append_graph(ld,graph=graphs[0] if graphs is not None and len(graphs)>0 else None)
         else:
            update_graph(ld,graph=graphs[0] if graphs is not None and len(graphs)>0 else None)
         return ('',201)
      elif request_type[0]=='application/sparql-query':
         if request.method=='PUT':
            abort(400,'Invalid operation with SPARQL query.')
         ld = query(request.text,graphs=request.args.getlist('graph'))
         return jsonld_response(jsonld.compact(ld,current_app.config.get('LD_CONTEXT')))
      else:
         abort(400,'Unrecognized media type: '+request_type[0])

@data.route('/<graph>/',methods=['GET','POST','PUT'])
def retrieve_graph(graph):
   if request.method=='GET':
      subjects = request.args.getlist('subject')
      ld = get([graph],subjects)
      return jsonld_response(jsonld.compact(ld,current_app.config.get('LD_CONTEXT')))
   else:
      request_type = content_type()
      if request_type[0]=='application/ld+json':
         json = request.get_json(force=True)
         ld = jsonld.compact(json,current_app.config.get('LD_CONTEXT'))
         if request.method=='POST':
            append_graph(ld,graph=graph)
         else:
            update_graph(ld,graph=graph)
         return ('',201)
      elif request_type[0]=='application/sparql-query':
         if request.method=='PUT':
            abort(400,'Invalid operation with SPARQL query.')
         ld = query(request.text,graphs=[graph])
         return jsonld_response(jsonld.compact(ld,current_app.config.get('LD_CONTEXT')))
         return jsonld_response(ld)
      else:
         abort(400,'Unrecognized media type: '+request_type[0])
