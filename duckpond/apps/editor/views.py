from flask import render_template, redirect, session, request, url_for, escape, flash, g
from functools import wraps
from .app import app, users
from .forms import LoginForm
from . import model

@app.route('/')
def index():
   works = model.getCreativeWorks()
   return render_template('home.html',
                           title='Editor',
                           username=session['username'],
                           works=works)

@app.route('/login', methods=['GET', 'POST'])
def login():
   if 'username' in session:
      username = session['username']
      if users.validate(username):
         return redirect(url_for('index'))
   form = LoginForm()
   if form.validate_on_submit():
      g.user = users.login(form.username.data,form.password.data)
      if g.user is not None:
         flash('Login for {} successful.'.format(form.username.data))
         session['username'] = form.username.data
         return redirect('/')
      else:
         flash('Login for {} failed.'.format(form.username.data))
   return render_template('login.html',
                           title='Sign In',
                           form=form)

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.clear()
    return redirect(url_for('index'))
