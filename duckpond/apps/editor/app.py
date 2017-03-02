from flask import Flask, request, g, session, redirect, abort
from datetime import datetime
from flask.ext.session import Session

app = Flask(__name__)
app.config.from_envvar('WEB_CONF')
Session(app)

@app.before_request
def before_request():
   if 'username' in session:
      username = session['username']
      g.user = app.config['AUTH_SERVICE'].getUser(username)
   authenticated = 'user' in g and g.user is not None

   if request.path.startswith('/assets'):
      return
   if (request.path == '/' or request.path == '/logout') and not authenticated:
      return redirect('/login')
   if request.path != '/login' and not authenticated:
      abort(401)
