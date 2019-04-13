import sqlite3 as sql
from os import path
from app import db, login_manager
from datetime import datetime
from flask_login import UserMixin, current_user
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from sqlalchemy.orm import sessionmaker
from app.users.forms import UpdateTriggerForm
from app.search import add_to_index, remove_from_index, query_index


ROOT = path.dirname(path.relpath((__file__)))

class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)

db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)

friends = db.Table('friends',
    db.Column('friend_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('friended_id', db.Integer, db.ForeignKey('user.id')),
)

@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))

class User( db.Model, UserMixin):
  __searchable__ = ['username']
  id = db.Column(db.Integer, primary_key = True)
  username = db.Column(db.String(20), unique=True, nullable=False)
  email = db.Column(db.String(120), unique=True, nullable=False)
  image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
  password = db.Column(db.String(60), nullable=False)
  shaving = db.Column(db.Integer, nullable=False, default=0)
  last_seen = db.Column(db.DateTime, default=datetime.utcnow)  
  
  thresholds = db.relationship("Threshold", back_populates="user")
  todos = db.relationship("Todo", back_populates="user")

  friended = db.relationship(
                            'User', secondary=friends,
                            primaryjoin=(friends.c.friend_id == id),
                            secondaryjoin=(friends.c.friended_id == id),
                            backref=db.backref('friends', lazy='dynamic'), lazy='dynamic')

  messages_sent = db.relationship('Message',
                                    foreign_keys='Message.sender_id',
                                    backref='author', lazy='dynamic')
  messages_received = db.relationship('Message',
                                      foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic')
  last_message_read_time = db.Column(db.DateTime)
  

  def get_reset_token(self, expires_sec=1800):
    s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
    return s.dumps({'user_id': self.id}).decode('utf-8')

  @staticmethod
  def verify_reset_token(token):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
      user_id = s.loads(token)['user_id']
    except:
      return None
    return User.query.get(user_id)

  def __repr__(self):
    return f"User('{self.username}', '{self.email}','{self.image_file}', '{self.friended}')"

  def friend(self, user):
    form = UpdateTriggerForm
    if not self.is_friending(user):
      threshold = Threshold(user_id=current_user.id, t_hold=0, friend=user.id)
      db.session.add(threshold)
      db.session.commit()
      self.friended.append(user)

  def unfriend(self, user):
    if self.is_friending(user):
      tHolds = db.session.query(Threshold).filter(Threshold.user_id == current_user.id)
      for thold in tHolds:
        if thold.friend == user.id:
          db.session.delete(thold)
      db.session.commit()
      self.friended.remove(user)

  def is_friending(self, user):
    return self.friended.filter(
        friends.c.friended_id == user.id).count() > 0

  def new_messages(self):
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(
            Message.timestamp > last_read_time).count()


class Threshold(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
  t_hold = db.Column(db.Integer, nullable=False, default=0)
  friend = db.Column(db.Integer, nullable=False) 

  user = db.relationship("User", back_populates="thresholds")

  def __repr__(self):
    return f"Threshold('{self.id}', '{self.user_id}','{self.t_hold}', '{self.friend}')"

class Todo(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  text = db.Column(db.String(200))
  complete = db.Column(db.Boolean)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
  date_made = db.Column(db.String(200))
  date_due = db.Column(db.String(200))

  user = db.relationship("User", back_populates="todos")

  def __repr__(self):
    return f"Todo('{self.id}', '{self.user_id}','{self.complete}', '{self.text}')"

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return '<Message {}>'.format(self.body)
