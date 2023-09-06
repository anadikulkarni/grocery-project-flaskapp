from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import json

with open("config.json") as config:
    configdata = json.load(config)
    
app = Flask(__name__)
app.config['SECRET_KEY'] = configdata['SECRETKEY']
app.config["SQLALCHEMY_DATABASE_URI"] = configdata["SQLALCHEMY_DATABASE_URI"]

db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), unique = True, nullable = False)
    password = db.Column(db.String(60), nullable = False)

class Manager(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(20), unique = True, nullable = False)
    password = db.Column(db.String(60), nullable = False)
    
with app.app_context():
    db.create_all()


