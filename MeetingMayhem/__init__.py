"""
File: __init__.py
Author: Robert Shovan /Voitheia
Date Created: 6/15/2021
Last Modified: 6/24/2021
E-mail: rshovan1@umbc.edu
Description: python file that manages the Meeting Mayhem package
This file does a lot of initialization of things that are used later
"""

"""
info about imports
flask - import flask because we kinda need that for a flask app
SQLAlchemy - makes managing the database easy
Bcrypt - does password hashing fun stuff
LoginManager - login manager login manager manages login :)
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_socketio import SocketIO

#initialize the flask app
app = Flask(__name__)

#secret key helps protect against XSRF attacks
app.config['SECRET_KEY'] = '135d1e15e1d736b415725bd01a0aafed'

socketio = SocketIO(app)

#tell sqlalchemy where the database file is
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

#initialize the database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#initialize the password hashing lad
bcrypt = Bcrypt(app)

#login manager login manager manages login
login_manager = LoginManager(app)

#needed for redir on accessing page you need to login for
login_manager.login_view = 'login'

#make the "please login" message pretty
login_manager.login_message_category = 'info'

#this import is done here to prevent circular imports
from MeetingMayhem import routes