from flask import Blueprint, g
from app.models import User, Todo
from app import  db, bcrypt, mail
from flask import render_template, request, url_for, flash, redirect, abort
from app.users.forms import (registrationForm, loginForm,
                        UpdateAccountForm, RequestResetForm, 
                        ResetPasswordForm, TodosForm)
from flask_login import login_user, current_user, logout_user, login_required
import secrets
import os
from PIL import Image
from flask_mail import Message
from datetime import datetime
from flask_babel import _, get_locale


main = Blueprint('main', __name__)


@main.route('/home', methods=['GET', 'POST'])
def index():
  return render_template('index.html')

@main.route('/friends')
def friends():
  page = request.args.get('page', 1, type=int)
  users = User.query.order_by(User.username).paginate(page=page, per_page=5)
  if not current_user.is_authenticated:
    return redirect(url_for('users.register'))
  else:
    return render_template('friends.html', title="friends", users=users, current_page=page)

@main.route('/')
def about():
  return render_template('about.html')

@main.route('/Todo', methods=['GET', 'POST'])
def todo():
  if not current_user.is_authenticated:
    return redirect(url_for('users.register'))
  else:
    todos = Todo.query.filter_by(user_id=current_user.id)
    form = TodosForm(todos=todos)
    if request.method == "POST":
      if form.new_todo[0].date_due.data and form.new_todo[0].text.data != "Enter your to do item here":
        todo = Todo(text=form.new_todo[0].text.data, complete=False, date_due=str(form.new_todo[0].date_due.data), user_id=current_user.id)
        db.session.add(todo)
        db.session.commit()
        flash(_('Your to do has been create!'), 'success')

      for Form in form.todos:
        if Form.complete.data == True:
          for TODO in todos:
            if TODO.id == Form.iden.data:
              db.session.delete(TODO)
              db.session.commit()
              flash('You have completed the task {}'.format(Form.text.data),  'danger')

      return redirect(url_for('main.todo'))

    return render_template('todo.html', title='Todo', form=form, todos=todos)


