from flask import Blueprint
from flask import send_from_directory, render_template, abort, current_app, Response, stream_with_context
import requests
import os, io

docs = Blueprint('duckpond_blog_docs',__name__)

@docs.route('/docs/<path:path>')
def send_doc(path):
   siteURL = current_app.config.get('SITE_URL')

   templateOptions = current_app.config.get('TEMPLATE_OPTIONS')
   if templateOptions is None:
      templateOptions = {
         'title' : 'My Journal'
      }

   location = current_app.config.get('DOCS')
   if location is None:
      abort(404)

   if location[0:4]=='http':
      url = location + path
      req = requests.get(url, stream = True,headers={'Connection' : 'close'})
      if req.headers['Content-Type'][0:9]=='text/html':
         return render_template('content.html', siteURL=siteURL if siteURL is not None else request.url_root[0:-1], options=templateOptions, html=req.text, entry=None)
      else:
         return Response(stream_with_context(req.iter_content()), headers = dict(req.headers))

   else:

      dir = os.path.abspath(location)
      if path.endswith('.html'):

         glob = io.StringIO()
         try:
            with open(os.path.join(dir,path), mode='r', encoding='utf-8') as doc:
               peeked = doc.readline()
               if peeked.startswith('<!DOCTYPE'):
                  return send_from_directory(dir, path)
               glob.write(peeked)
               for line in doc:
                  glob.write(line)

               return render_template('content.html', siteURL=siteURL if siteURL is not None else request.url_root[0:-1], options=templateOptions, html=glob.getvalue(), entry=None)
         except FileNotFoundError:
            abort(404)

      return send_from_directory(dir, path)
