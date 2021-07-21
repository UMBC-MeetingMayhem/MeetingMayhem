"""
File: models.py
Author: Robert Shovan /Voitheia
Date Created: 6/15/2021
Last Modified: 7/21/2021
E-mail: rshovan1@umbc.edu
Description: python file that handles the database
"""

"""
info about imports
db, login_manager - import from __init__.py the database and login manager so we can put users in the database and do login stuff
UserMixin - does some magic so that handling user login is easy
partial, orm - used for getUserFactory for the dropdown menus in writing messages
"""
from Meeting_Mayhem import db, login_manager
from flask_login import UserMixin
from functools import partial
from sqlalchemy import orm
#all this code is basically creating the tables for the database

#login management
@login_manager.user_loader #tells login manager that this is the user loader function
def load_user(user_id):
    return User.query.get(int(user_id))

#i feel like fields and variables are pretty self explanatory for the models
#user table
#contains information about the user
#might need to be updated later to include metrics, or maybe metrics can be its own model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.Integer, nullable=False) #dictates what role the account is
    """
    roles: 1 - admin, 2 - GM, 3 - adversary, 4 - user, 5 - spectator
    admin: is able to changes the roles of the users incase we need to do this
    GM: game master, puts different users and adversaries into a specific game instance
    adversary: edits messages from users
    user: plays the game
    spectator: is able to see results for game, probably also messages for each round
    we might also want to make a role thats both an adversary and a user at some point
    """
    
    def __repr__(self): #this is what gets printed out for the User when a basic query is run
        return f"User('{self.id}','{self.username}','{self.email}','{self.password}','{self.role}')"

#this is how the message forms pulls the users it needs for the recipient dropdown, I don't really know how it works lol
#https://stackoverflow.com/questions/26254971/more-specific-sql-query-with-flask-wtf-queryselectfield
def getUser(columns=None):
    u = User.query.filter_by(role=4)
    #TODO: once fuctionality for multiple games is added, we need to also filter by the game session
    #this will also keep the admin and GM users from getting included in the dropdown
    #this should allow us to be able to choose which users come up in the dropdown
    if columns:
        u = u.options(orm.load_only(*columns))
    return u

def getUserFactory(columns=None):
    return partial(getUser, columns=columns)

#message table
#contains the messages that users send to each other and the adversary
#two sets of sender, recipient, content so that when the adversary edits a message, we can see both the before and after
#is_edited indicates if the message has been edited
#also used for a message that the adversary wrote, is_edited will be true without any content in the secondary sender/recipient/content in that case
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round = db.Column(db.Integer, nullable=False) #keeps track of which round the message was created on
    sender = db.Column(db.Integer, db.ForeignKey('user.username'), nullable=False)
    recipient = db.Column(db.Integer, db.ForeignKey('user.username'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_edited = db.Column(db.Boolean, nullable=False)
    new_sender = db.Column(db.Integer, db.ForeignKey('user.username'), nullable=True)
    new_recipient = db.Column(db.Integer, db.ForeignKey('user.username'), nullable=True)
    edited_content = db.Column(db.Text, nullable=True)
    
    def __repr__(self): #this is what gets printed out for the message, just spits out everything
        return f"Message('{self.id}','{self.round}','{self.sender}','{self.recipient}','{self.content}','{self.is_edited}','{self.new_sender}','{self.new_recipient}','{self.edited_content}')"

#metadata table, name subject to change to something like "Gamestate"
#include information about the game in here so it can by dynamically pulled
#also allows for scaling once we allow for multiple game sessions
class Metadata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    adversary = db.Column(db.Integer, db.ForeignKey('user.username'), nullable=False)
    current_round = db.Column(db.Integer, nullable=False)
    adv_current_msg = db.Column(db.Integer, nullable=False)
    adv_current_msg_list_size = db.Column(db.Integer, nullable=False)

    def __repr__(self): #this is what gets printed out for the metadata, just spits out everything
        return f"Metadata('{self.id}','{self.adversary}','{self.current_round}','{self.adv_current_msg}','{self.adv_current_msg_list_size}',)"

"""

-----------------------info about database stuff with python-----------------------
 this section should probably be moved to not here 
run python in powershell prompt

from <filename> import db (ex: from Meeting_Mayhem import db)
from <filename> import User (ex: from Meeting_Mayhem.models import User, Message)
-these imports allow us to use the classes and db on the python command line

db.create_all()
-creates all the tables needed for the db

user_1 = User(username='bob', email='bob@gmail.com', password='password')
-this creates a user variable

db.session.add(user_1)
-this adds the user we created to the "stack" that is waiting to be committed to the db

user_2 = User(username='joe', email='joe@gmail.com', password='password')
db.session.add(user_2)
db.session.commit()
-commits the users we added to the "stack" to the db

User.query.all()
-querys the database for all users

User.query.first()
-gets the first user

User.query.filter_by(username='bob').all()
-querys the database for all users with username of 'bob'

user = User.query.filter_by(username='bob').first()
-puts the bob user into a variable of "user"

user
-will print out the information of the user in the user variable

user.id
-will print out the id of the user in the user variable

user = User.query.get(2)
-sets the user variable to the user of id 2

post_1 = Post(title='thingy', content='this has stuff in it yeee', user_id=user.id)
-makes a new post variable with information in it that has an author of the user variable

db.drop_all()
-drops all tables

Message.query.delete()
-deletes all entrys in the message table, also need to do a commit so changes take place

change the role of a user:
    adv = User.query.filter_by(username='adversary').first()
    adv.role = 3
    db.session.commit()

"""