import json
from flask import make_response
from .app import app
from . import model

def jsonld_response(data):
   response = make_response(data)
   response.headers['Content-Type'] = "application/ld+json; charset=utf-8"
   return response

@app.route('/data/content/')
def content():
   works = model.getCreativeWorks()
   return jsonld_response(json.dumps(works));
