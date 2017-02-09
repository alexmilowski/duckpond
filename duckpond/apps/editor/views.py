from flask import render_template, redirect, session, request, url_for, escape, flash, g
from functools import wraps
from .app import app
from .forms import LoginForm
from . import model

@app.route('/')
def index():
   return render_template('home.html',
                           title='Duckpond Content Editor',
                           username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
   if 'username' in session:
      redirect(url_for('index'))
   form = LoginForm()
   if form.validate_on_submit():
      username = form.username.data
      password = form.password.data
      if app.config['AUTH_SERVICE'].authenticate(username,password):
         g.user = app.config['AUTH_SERVICE'].getUser(username)
      if g.user is not None:
         flash('Login for {} successful.'.format(username))
         session['username'] = username
         return redirect('/')
      else:
         flash('Login for {} failed.'.format(username))
   return render_template('login.html',
                           title='Sign In',
                           form=form)

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.clear()
    return redirect(url_for('index'))
