from app import create_app
from app import db

app = create_app(db)

with app.app_context():
  db.create_all()