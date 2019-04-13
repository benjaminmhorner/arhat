from flask import Blueprint, g
from flask_login import current_user
from flask import redirect, url_for
from app.users.forms import (registrationForm, loginForm,
                        UpdateAccountForm, RequestResetForm, 
                        ResetPasswordForm,
                        UpdateTriggerForm,
                        TriggersForm, SearchForm, MessageForm)
from app import  db, bcrypt, mail
from app.models import User, friends, Threshold, Todo
from flask import render_template, request, url_for, flash, redirect, abort,current_app
from flask_login import login_user, current_user, logout_user, login_required
import os
from PIL import Image
from flask_mail import Message
from app.users.utils import save_picture, send_reset_email
from sqlalchemy.orm import Session
from datetime import datetime
from flask_babel import get_locale, _
from app.models import Message



users = Blueprint('users', __name__)

@users.before_app_request
def before_request():
    if current_user.is_authenticated:
      current_user.last_seen = datetime.utcnow()
      db.session.commit()
      g.user = current_user
      #g.search_form = SearchForm()
      todos = Todo.query.filter_by(user_id=current_user.id)
      total = 0
      for i, t in enumerate(todos):
        if int(str(current_user.last_seen)[8:10]) > int(t.date_due[8:10]) and int(str(current_user.last_seen)[5:7]) >= int(t.date_due[5:7]) and int(str(current_user.last_seen)[0:4]) >= int(t.date_due[0:4]):
          total += 1
        elif int(str(current_user.last_seen)[5:7]) >= int(t.date_due[5:7]) and int(str(current_user.last_seen)[0:4]) >= int(t.date_due[0:4]):
          total += 1
        elif int(str(current_user.last_seen)[0:4]) >= int(t.date_due[0:4]):
          total += 1
      if total != 0:
        dep_perc = (100/i) * total
        text = "Please contact {} he feels like poo".format(current_user.username)
        tHolds = db.session.query(Threshold).filter(Threshold.user_id == current_user.id)
        users = User.query.order_by(User.username)
        Friends = []
        for user in users:
          if current_user.is_friending(user):
            Friends.append(user)
        for i, thold in enumerate(tHolds):
          if thold.t_hold != 0 and thold.t_hold <= dep_perc:
            msg = Message(author=current_user, recipient=Friends[i], body=text)
            db.session.add(msg)
            db.session.commit()
      else:
        dep_perc = 0
    g.locale = str(get_locale())
   


@users.route('/register', methods=['GET', 'POST'])
def register():
  if current_user.is_authenticated:
    return redirect(url_for('main.index'))
  form = registrationForm()
  if form.validate_on_submit():
    hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
    user = User(username=form.username.data, email=form.email.data, password=hashed_password)
    db.session.add(user)
    db.session.commit()
    flash(f'Account created for {form.username.data}! You can now log in', 'success')
    return redirect(url_for('users.login'))
  return render_template('register.html', title='register', form=form)

@users.route('/login', methods=['GET', 'POST'])
def login():
  if current_user.is_authenticated:
    return redirect(url_for('main.index'))
  form = loginForm()
  if form.validate_on_submit():
    user = User.query.filter_by(email=form.email.data).first()
    if user and bcrypt.check_password_hash(user.password, form.password.data):
      login_user(user, remember=form.remember.data)
      next_page = request.args.get('next')
      return redirect(next_page) if next_page else redirect(url_for('main.index'))
    else:
      flash('login failed bro', 'danger')
  return render_template('login.html', title='login', form=form)

@users.route('/logout', methods=['POST'])
def logout():
  logout_user()
  return redirect(url_for('users.login'))

@users.route('/account', methods=['GET', 'POST'])
@login_required
def account():
  form = UpdateAccountForm()
  if form.validate_on_submit():
    if form.picture.data:
      pic = current_user.image_file
      if pic != 'default.jpg':
        os.remove(os.path.join(current_app.root_path,'static/profile_pics/', current_user.image_file))
      picture_file = save_picture(form.picture.data)
      current_user.image_file = picture_file
    current_user.username = form.username.data
    current_user.email = form.email.data
    db.session.commit()
    flash('Your account has been updated fam', 'success')
    return redirect(url_for('users.account'))
  elif request.method =='GET':
    form.username.data = current_user.username
    form.email.data = current_user.email
  image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
  return render_template('account.html', title='account', image_file=image_file, form=form)

@users.route('/home', methods=['GET', 'POST'])
def triggers():
  users = User.query.order_by(User.username)
  Friends = []
  if not current_user.is_authenticated:
    return redirect(url_for('users.register'))
  else:
    for user in users:
      if current_user.is_friending(user):
        Friends.append(user)
    tHolds = db.session.query(Threshold).filter(Threshold.user_id == current_user.id)
    form = TriggersForm(triggers=tHolds)
    if request.method == 'POST':
      current_user.shaving = form.triggers[0].shaving.data
      for i, tHold in enumerate(tHolds):
        tHold.id = tHold.id
        tHold.t_hold = form.triggers[i].t_hold.data
        tHold.user_id = current_user.id
        tHold.friend = form.triggers[i].friend.data
        db.session.commit()
      
      flash('Your settings have been updated fam', 'info')
      return redirect(url_for('main.index'))

    return render_template('index.html', title='index', form=form, tHolds=tHolds, Friends=Friends, users=users)
  




@users.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
  if current_user.is_authenticated:
    return redirect(url_for('main.index'))
  form = RequestResetForm()
  if form.validate_on_submit():
    user = User.query.filter_by(email=form.email.data).first()
    send_reset_email(user)
    flash('An email has been sent with instructions to reset your password', 'info')
    return redirect(url_for('users.login'))
  return render_template('users.reset_request.html', title = 'Reset Password', form=form)

@users.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
      return redirect(url_for('main.index'))
    user = User.verify_reset_token(token)
    if user is None:
      flash('That is an invalid or expired token', 'warning')
      return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
      hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
      user.password = hashed_password
      db.session.commit()
      flash(f'Your password has been updated', 'success')
      return redirect(url_for('users.login'))
    return render_template('reset_token.html', title = 'Reset Password', form=form)


@users.route('/friend/<username>')
@login_required
def friend(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.friends'))
    if user == current_user:
        flash('You cannot be friends yourself!')
        return redirect(url_for('main.friends', username=username))
    current_user.friend(user)
    db.session.commit()
    flash('You are friends {}!'.format(username), 'success')
    return redirect(url_for('main.friends', username=username))

@users.route('/unfriend/<username>')
@login_required
def unfriend(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for('main.friends'))
    if user == current_user:
        flash('You cannot be friends with yourself!')
        return redirect(url_for('main.friends', username=username))
    current_user.unfriend(user)
    db.session.commit()
    flash('You are not friends with {}.'.format(username), 'warning')
    return redirect(url_for('main.friends', username=username))


@users.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('main.friends'))
    page = request.args.get('page', 1, type=int)
    users, total = User.search(str(g.search_form.q.data)+"*", page,
                               current_app.config['USERS_PER_PAGE'])
    next_url = url_for('app.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['USERS_PER_PAGE'] else None
    prev_url = url_for('app.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template('search.html', title=_('Search'), users=users,
                           next_url=next_url, prev_url=prev_url)
    

@users.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        db.session.commit()
        flash(_('Your message has been sent.'), 'success')
        return redirect(url_for('main.friends', username=recipient))
    return render_template('send_message.html', title=_('Send Message'),
                           form=form, recipient=recipient)

@users.route('/messages')
@login_required
def messages():
    current_user.last_message_read_time = datetime.utcnow()
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['USERS_PER_PAGE'], False)
    sent = current_user.messages_sent.order_by(
        Message.timestamp.desc())
    next_url = url_for('users.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('users.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template('messages.html', messages=messages.items,
                           next_url=next_url, prev_url=prev_url, sent=sent)
