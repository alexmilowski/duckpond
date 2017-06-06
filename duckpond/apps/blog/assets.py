from flask import Blueprint
from flask import send_from_directory, current_app

assets = Blueprint('duckpond_blog_assets',__name__)
@assets.route('/assets/<path:path>')
def send_asset(path):
   dir = current_app.config.get('ASSETS')
   if dir is None:
      dir = __file__[:__file__.rfind('/')] + '/assets/'
   return send_from_directory(dir, path)
