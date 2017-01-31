import json
import os
from flask import make_response, request, Response
from .app import app
from . import model

def jsonld_response(data):
   response = make_response(data)
   response.headers['Content-Type'] = "application/ld+json; charset=utf-8"
   return response

@app.route('/data/content/',methods=['GET','POST'])
def content():
   if request.method == 'GET':
      works = model.getContentList()
      return jsonld_response(json.dumps(works))

   if request.method == 'POST':
      # Parse the incoming JSON-LD data
      force = request.headers['Content-Type'].startswith('application/ld+json')
      data = request.get_json(force=force)
      if data is None:
         abort(400)
      if 'name' not in data or \
         'genre' not in data or \
         'headline' not in data or \
         '@type' not in data:
         abort(400)
      status,url = model.createContent(data['@type'],data['genre'],data['name'],data['headline'])
      return Response(status=status,headers=({'Location' : url} if status==201 else {}))

@app.route('/data/content/<id>/',methods=['GET','PUT','POST','DELETE'])
def content_item(id):

   if request.method == 'GET':
      content = model.getContent(id)
      return jsonld_response(json.dumps(content))

   if request.method == 'POST':
      abort(400)

   if request.method == 'PUT':
      abort(400)

   if request.method == 'DELETE':
      status = model.deleteContent(id)
      return Response(status=status)

@app.route('/data/content/<id>/<resource>',methods=['DELETE'])
def content_item_resource(id,resource):
   status = model.deleteContentResource(id,resource)
   return Response(status=status)


@app.route('/data/content/<id>/upload/<property>',methods=['POST'])
def content_item_resource_upload(id,property):
   #print(request.headers['Content-Type'])
   #print(request.files)
   file = request.files['file']
   print(file.filename)
   print(file.content_type)
   print(file.content_length)
   uploadDir = app.config['UPLOAD_STAGING'] if 'UPLOAD_STAGING' in app.config else 'tmp'
   os.makedirs(uploadDir,exist_ok=True)
   staged = os.path.join(uploadDir, file.filename)
   file.save(staged)
   status = 500
   with open(staged,"rb") as data:
      status = model.uploadContentResource(id,property,file.filename,file.content_type,os.path.getsize(staged),data)
   os.unlink(staged)
   return Response(status=status)
