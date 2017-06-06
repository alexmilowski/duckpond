from flask import Blueprint
from flask import send_from_directory, render_template, abort, current_app
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

   dir = current_app.config.get('DOCS')
   if dir is None:
      abort(404)
   dir = os.path.abspath(dir)

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
