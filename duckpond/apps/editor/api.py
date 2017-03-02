import json, os, io
from flask import make_response, request, Response, stream_with_context, abort
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
      status,url,modified = model.createContent(data['@type'],data['genre'],data['name'],data['headline'])
      return Response(status=status,headers=({'Location' : url, 'Date-Modified' : modified} if status==201 else {}))

@app.route('/data/content/<id>/',methods=['GET','PUT','POST','DELETE'])
def content_item(id):

   if request.method == 'GET':
      content = model.getContent(id)
      return jsonld_response(json.dumps(content))

   if request.method == 'POST':
      abort(400)

   if request.method == 'PUT':
      force = request.headers['Content-Type'].startswith('application/ld+json')
      data = request.get_json(force=force)
      if data is None:
         abort(400)
      status_code,data,contentType = model.updateContent(id,data);
      if status_code==200:
         return Response(stream_with_context(data),content_type = contentType)
      else:
         abort(status_code)

   if request.method == 'DELETE':
      status = model.deleteContent(id)
      return Response(status=status)

@app.route('/data/content/<id>/<resource>',methods=['GET','PUT','DELETE'])
def content_item_resource(id,resource):
   if request.method == 'GET':
      wrap = request.args.get('wrap')
      status_code,data,contentType = model.getContentResource(id,resource);
      if status_code==200:
         if contentType.startswith("text/html") and wrap is not None:
            blob = io.BytesIO()
            for chunk in data:
               blob.write(chunk)
            content = blob.getvalue().decode("utf-8").strip()
            if not content.startswith('<!DOCTYPE'):
               editorConfig = app.config.get('EDITOR_CONFIG')
               header = ''
               bodyStart = ''
               bodyEnd = ''
               if editorConfig is not None and wrap=='preview':
                  wheader = editorConfig.get('wrap-header')
                  pheader = editorConfig.get('preview-wrap-header')
                  if pheader is not None:
                     header = pheader
                  elif wheader is not None:
                     header = wheader
                  wbody = editorConfig.get('wrap-body')
                  pbody = editorConfig.get('preview-body-main')
                  if pbody is not None:
                     bodyStart = pbody[0]
                     bodyEnd = pbody[1]
                  elif wbody is not None:
                     bodyStart = wbody[0]
                     bodyEnd = wbody[1]
               elif editorConfig is not None and wrap=='formatted':
                  wheader = editorConfig.get('wrap-header')
                  if wheader is not None:
                     header = wheader
                  wbody = editorConfig.get('wrap-body')
                  if wbody is not None:
                     bodyStart = wbody[0]
                     bodyEnd = wbody[1]
               content = """
<!DOCTYPE html>
<html>
<head><title>""" + resource + '</title>' + header + """
</head>
<body>
""" + bodyStart + content + bodyEnd + '</body></html>'
            return Response(stream_with_context(content),content_type = contentType)
         else:
            return Response(stream_with_context(data),content_type = contentType)
      else:
         abort(status_code)
   if request.method == 'PUT':
      status_code,data,contentType = model.updateContentResource(id,resource,request.headers['Content-Type'],request.stream);
      if status_code==200 or status_code==201:
         return Response(stream_with_context(data),status=status_code,content_type = contentType)
      else:
         return Response(status=status)

   if request.method == 'DELETE':
      status = model.deleteContentResource(id,resource)
      return Response(status=status)


@app.route('/data/content/<id>/upload/<property>',methods=['POST'])
def content_item_resource_upload(id,property):
   #print(request.headers['Content-Type'])
   #print(request.files)
   file = request.files['file']
   #print(file.filename)
   #print(file.content_type)
   #print(file.content_length)
   uploadContentType = file.content_type
   if file.content_type.startswith("text/") and file.content_type.find("charset=")<0:
      uploadContentType = file.content_type+"; charset=UTF-8"
   uploadDir = app.config['UPLOAD_STAGING'] if 'UPLOAD_STAGING' in app.config else 'tmp'
   os.makedirs(uploadDir,exist_ok=True)
   staged = os.path.join(uploadDir, file.filename)
   file.save(staged)
   status = 500
   responseJSON = None
   contentType = None
   with open(staged,"rb") as data:
      status,responseJSON,contentType = model.uploadContentResource(id,property,file.filename,uploadContentType,os.path.getsize(staged),data)
   os.unlink(staged)
   if status==200 or status==201:
      return Response(stream_with_context(responseJSON),status=status,content_type = contentType)
   else:
      return Response(status=status)
