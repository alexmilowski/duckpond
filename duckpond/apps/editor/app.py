from flask import Flask, request, g, session, redirect, abort
from datetime import datetime
from flask.ext.session import Session

app = Flask(__name__)
app.config.from_envvar('WEB_CONF')
Session(app)

class Users:
   loggedIn = {}
   def validate(self,username):
      if username in self.loggedIn:
         info = self.loggedIn[username]
         delta = info['at'] - datetime.now()
         if delta.total_seconds()>(60*30):
            del self.loggedIn[username]
         else:
            info['at'] = datetime.now()
         return app.config['AUTH_SERVICE'].getUser(username)
      return None
   def login(self,username,password):
      if app.config['AUTH_SERVICE'].authenticate(username,password):
         if username in self.loggedIn:
            info = self.loggedIn[username]
            info['at'] = datetime.now()
         else:
            self.loggedIn[username] = { 'at': datetime.now() }
         return app.config['AUTH_SERVICE'].getUser(username)
      else:
         return None

users = Users()


@app.before_request
def before_request():
   if 'username' in session:
      username = session['username']
      g.user = users.validate(username)
      if g.user is None:
         session.clear()
   authenticated = 'user' in g and g.user is not None

   if request.path.startswith('/assets'):
      return
   if request.path != '/login' and not authenticated:
      return redirect('/login')
