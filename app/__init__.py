from flask import Flask, request, current_app
from flask_cors import CORS 
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from app.config import Config
from flask_migrate import Migrate
from elasticsearch import Elasticsearch
from flask_babel import Babel
from flask import request
from flask_moment import Moment
from flask_bootstrap import Bootstrap






db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
mail = Mail()
bootstrap = Bootstrap()
moment = Moment()
babel = Babel()



def create_app(config_class=Config):
  app = Flask(__name__)
  app.config.from_object(Config)
  app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
    if app.config['ELASTICSEARCH_URL'] else None
  

  db.init_app(app)
  bcrypt.init_app(app)
  login_manager.init_app(app)
  mail.init_app(app)
  migrate = Migrate(app, db)
  bootstrap.init_app(app)
  moment.init_app(app)
  babel.init_app(app)

  from app.users.routes import users
  from app.main.routes import main
  from app.errors.handlers import errors
  app.register_blueprint(users)
  app.register_blueprint(main)
  app.register_blueprint(errors)


  return app

@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])


from app import models

