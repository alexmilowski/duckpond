from flask import send_from_directory
from .app import app

@app.route('/assets/<path:path>')
def send_asset(path):
   dir = __file__[:__file__.rfind('/')] + '/assets/'
   return send_from_directory(dir, path)
