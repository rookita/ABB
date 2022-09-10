from flask_sqlalchemy import SQLAlchemy

from __init__ import app

db = SQLAlchemy(app)

class All_Auctions(db.Model):
    aid = db.Column(db.Integer, primary_key = True, unique = True, nullable = False)
    seller = db.Column(db.String(128), default ="")
    addr = db.Column(db.String(128,collation="NOCASE"), default ="")
    state = db.Column(db.String(128),default = "commit") #commit,reveal,end
    item =  db.Column(db.String(128),default = "")
    start_reveal_time =  db.Column(db.Integer, default = 0)    
    DDL =  db.Column(db.Integer, default = 0)    
    winner = db.Column(db.String(128,collation="NOCASE"), default ="None")
    price =  db.Column(db.Integer, default = 0)    
    
class Users(db.Model):
    username = db.Column(db.String(128), primary_key=True, unique=True, nullable=False)
    password = db.Column(db.String(128), default="")
    address = db.Column(db.String(128,collation="NOCASE"), default="")
    
class Relation(db.Model):
    username = db.Column(db.String(128), primary_key = True)
    addr = db.Column(db.String(128,collation="NOCASE"), primary_key = True)
    bid = db.Column(db.Integer,default = 0)