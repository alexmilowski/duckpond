from flask import render_template, redirect, session, request, url_for, escape, flash, g, make_response, stream_with_context, Response
from functools import wraps
import json
import requests
from .app import app
from .forms import LoginForm
from . import model

@app.route('/')
def index():
   return render_template('home.html',
                           title='Duckpond Content Editor',
                           username=session['username'])
@app.route('/config.json')
def config():
   config = app.config.get('EDITOR_CONFIG')
   if config is None:
      config = { 'wrap-header' : ''}
   response = make_response(json.dumps(config))
   response.headers['Content-Type'] = "application/json; charset=utf-8"
   return response


@app.route('/login', methods=['GET', 'POST'])
def login():
   if 'username' in session:
      return redirect('/')
   form = LoginForm()
   failed = False
   if form.validate_on_submit():
      username = form.username.data
      password = form.password.data
      if app.config['AUTH_SERVICE'].authenticate(username,password):
         g.user = app.config['AUTH_SERVICE'].getUser(username)
      try:
         if g.user is not None:
            flash('Login for {} successful.'.format(username))
            session['username'] = username
            print("rediect="+form.redirectonlogin.data)
            if form.redirectonlogin.data=='true':
               return redirect('/')
            else:
               return render_template('login-successful.html',
                                      title='Duckpond Content Editor',
                                      username=session['username'])
         else:
            flash('Login for {} failed.'.format(username))
            failed = True
      except AttributeError:
         flash('Login for {} failed.'.format(username))
         failed = True

   compact = request.args.get('compact')
   requestRedirect = request.args.get('redirect')
   form.redirectonlogin.data = requestRedirect if requestRedirect is not None else 'true'

   return render_template('login.html' if compact is None or compact=='false' else 'login-compact.html',
                           title='Sign In',
                           failed=failed,
                           form=form)

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.clear()
    return redirect(url_for('index'))

@app.route('/proxy/<name>/<path:path>')
def home(name,path):
   proxies = app.config.get('PROXIES')
   if proxies is None:
      abort(404)
   base = proxies.get(name)
   if base is None:
      abort(404)
   req = requests.get(base + path, stream = True)
   return Response(stream_with_context(req.iter_content()), content_type = req.headers['content-type'])
