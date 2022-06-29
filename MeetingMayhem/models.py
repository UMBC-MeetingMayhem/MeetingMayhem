"""
File: models.py
Author: Robert Shovan /Voitheia
Date Created: 6/15/2021
Last Modified: 7/21/2021
E-mail: rshovan1@umbc.edu
Description: python file that handles the database
Whenever you make a change to the models, I believe you need to reset the DB
"""

"""
info about imports
db, login_manager - import from __init__.py the database and login manager so we can put users in the database and do login stuff
UserMixin - does some magic so that handling user login is easy
partial, orm - used for getUserFactory for the dropdown menus in writing messages
"""
from operator import or_
from MeetingMayhem import db, login_manager
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
    game = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=True)
    
    """
    roles: 1 - admin, 2 - GM, 3 - adversary, 4 - user, 5 - spectator, 6 - inactive
    admin: is able to changes the roles of the users incase we need to do this
    GM: game master, puts different users and adversaries into a specific game instance
    adversary: edits messages from users
    user: plays the game
    spectator: is able to see results for game, probably also messages for each round
    inactive: removed from game, unable to play
    we might also want to make a role thats both an adversary and a user at some point
    """

    def __repr__(self): #this is what gets printed out for the User when a basic query is run
        return f"User(ID='{self.id}', Username='{self.username}', Email='{self.email}', Pwd Hash='{self.password}', Role='{self.role}', Game='{self.game}')\n"

#this is how the message forms pulls the users it needs for the recipient dropdown, I don't really know how it works lol
#https://stackoverflow.com/questions/26254971/more-specific-sql-query-with-flask-wtf-queryselectfield

#queryfactory for adversary, used for gm to pick adversary for a game
def getAdversary(columns=None):
    adv = User.query.filter_by(role=3)
    if columns:
        adv = adv.options(orm.load_only(*columns))
    return adv

def getAdversaryFactory(columns=None):
    return partial(getAdversary, columns=columns)

#queryfactory for all users and adversaries, use for gm to manage roles
def getAllUserAdversary(columns=None):
    adv = User.query.filter(or_(User.role.__eq__(3),User.role.__eq__(4)))
    if columns:
        adv = adv.options(orm.load_only(*columns))
    return adv

def getAllUserAdversaryFactory(columns=None):
    return partial(getAllUserAdversary, columns=columns)

#queryfactory for all non gm users, use for gm to manage roles
def getNonGMUsers(columns=None):
    adv = User.query.filter(User.role.__gt__(2))
    if columns:
        adv = adv.options(orm.load_only(*columns))
    return adv

def getNonGMUsersFactory(columns=None):
    return partial(getNonGMUsers, columns=columns)

#message table
#contains the messages that users send to each other and the adversary
#two sets of sender, recipient, content so that when the adversary edits a message, we can see both the before and after
#is_edited indicates if the message has been edited
#also used for a message that the adversary wrote, is_edited will be true without any content in the secondary sender/recipient/content in that case
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round = db.Column(db.Integer, nullable=False) #keeps track of which round the message needs to be displayed for users in
    game = db.Column(db.Integer, db.ForeignKey('game.id'), nullable=False)
    sender = db.Column(db.String, nullable=False)
    recipient = db.Column(db.String, nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_edited = db.Column(db.Boolean, nullable=False)
    new_sender = db.Column(db.String, nullable=True)
    new_recipient = db.Column(db.String, nullable=True)
    edited_content = db.Column(db.Text, nullable=True)
    is_deleted = db.Column(db.Boolean, nullable=False) #keeps track if the adversary "deleted" the message
    adv_created = db.Column(db.Boolean, nullable=False) #keeps track if the adversary made this message
    is_encrypted = db.Column(db.Boolean, nullable=False, default=False) #keeps track of whether the message is encrypted or not
    encryption_details = db.Column(db.String, nullable=False, default="Null") #keeps track of username of recipient(s) and which key was used to encrypt
    is_signed = db.Column(db.Boolean, nullable=False, default=False) #keeps track of whether the message is signed or not
    signed_details = db.Column(db.String, nullable=False, default="Null") #keeps track of username of sender and which key was used to sign
    adv_submitted = db.Column(db.Boolean, nullable=False, default=False) #keeps track of whether message has been seen and forwarded by the adv so user can see it
    time_sent = db.Column(db.String, nullable=False, default="Null") # keeps track of when a message was sent by initial sender
    time_recieved = db.Column(db.String, nullable=False, default="Null") # keeps track of when a message has been recieved by intended recipient
    initial_is_encrypted = db.Column(db.Boolean, nullable=False, default=False) # keeps track of whether message was initially encrypted or not
    initial_encryption_details = db.Column(db.String, nullable=False, default="Null") # keeps track of original encryption details
    initial_is_signed = db.Column(db.Boolean, nullable=False, default=False) # keeps track of whether message was initially signed or not
    initial_signed_details = db.Column(db.String, nullable=False, default="Null") # keeps track of original signed details
    time_meet = db.Column(db.String, default="Null") # keeps track of the time user chooses to meet
    location_meet = db.Column(db.String, default="Null") # keeps track of the location user chooses to meet
    def __repr__(self): #this is what gets printed out for the message, just spits out everything
        return f"Message(ID='{self.id}', Round='{self.round}', Game='{self.game}' Sender='{self.sender}', Recipient='{self.recipient}', Content='{self.content}', Edited='{self.is_edited}', New Sender='{self.new_sender}', New Recipient='{self.new_recipient}', New Content='{self.edited_content}', Deleted='{self.is_deleted}', Adv Created='{self.adv_created}', Encrypted='{self.is_encrypted}', Encryption Key='{self.encryption_details}', Signed='{self.is_signed}', Signature='{self.signed_details}', adv_submitted='{self.adv_submitted}', Meet Location='{self.location_meet}', Meet Time='{self.time_meet})\n"
        
#game table
#include information about the game in here so it can by dynamically pulled
#also allows for scaling once we allow for multiple game sessions
class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    is_running = db.Column(db.Boolean, nullable=False)
    adversary = db.Column(db.Integer, db.ForeignKey('user.username'), nullable=False)
    players = db.Column(db.String, nullable=False)
    current_round = db.Column(db.Integer, nullable=False)
    adv_current_msg = db.Column(db.Integer, nullable=False)
    adv_current_msg_list_size = db.Column(db.Integer, nullable=False)
    vote_ready = db.Column(db.String)
    votes = db.Column(db.String)
    who_voted = db.Column(db.String)
    adv_vote = db.Column(db.String)
    end_result = db.Column(db.String)

    def __repr__(self): #this is what gets printed out for the metadata, just spits out everything
        return f"Game(ID='{self.id}', Name='{self.name}', Running='{self.is_running}', Adversary='{self.adversary}', Players='{self.players}', Vote_ready='{self.vote_ready}', Who_voted='{self.who_voted}', votes='{self.votes}', adv_vote='{self.adv_vote}', end_result='{self.end_result}')\n" 

#queryfactory for games, used for gm to modify specific games
def getGame(columns=None):
    game = Game.query.filter_by(is_running=True)

    if columns:
        game = game.options(orm.load_only(*columns))
    return game

def getGameFactory(columns=None):
    return partial(getGame, columns=columns)


"""

-----------------------info about database stuff with python-----------------------
this section should probably be moved to not here
CREATING USERS THIS WAY IS INSECURE BECAUSE WE'RE COPYING THE PWD HASH, NOT HOW BCRYPT IS SUPPOSED TO WORK

run python in powershell prompt
------------------------------------------------------
from MeetingMayhem import db
from MeetingMayhem.models import User, Message, Game
------------------------------------------------------

from <filename> import db (ex: from MeetingMayhem import db)
from <filename> import User (ex: from MeetingMayhem.models import User, Message, Metadata)
-these imports allow us to use the classes and db on the python command line

db.create_all()
-creates all the tables needed for the db

user_1 = User(username='bob', email='bob@gmail.com', password='$2b$12$XKWaEWQnp8e/uyDroUMCOeiqe82jnNn7sJzAfhbEOr1Y0HquInu0', role=4)
-this creates a user variable

db.session.add(user_1)
-this adds the user we created to the "stack" that is waiting to be committed to the db

user_2 = User(username='joe', email='joe@gmail.com', password='$2b$12$XKWaEWQnp8e/uyDroUMCOeiqe82jnNn7sJzAfhbEOr1Y0HquInu0', role=4)
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

db.drop_all()
-drops all tables

Message.query.delete()
-deletes all entrys in the message table, also need to do a commit so changes take place

User.query.filter_by(id=123).delete()
-delete a user, make sure to commit

Change the role of a user:
adv = User.query.filter_by(username='adversary').first()
adv.role = 3
db.session.commit()

Reset DB:
from MeetingMayhem import db
from MeetingMayhem.models import User, Message, Game
db.drop_all()
db.session.commit()
db.create_all()

user creation:
gm = User(username='gmaster', email='gmaster@gmail.com', password='$2b$12$MIKYo2NKqRT9nhrKDr4MoeE5SPdEUgboaAziELzc6k2lTU24xuLtC', role=2)
adv = User(username='adv', email='adv@gmail.com', password='$2b$12$JdWTF/r7bfb9ijMoVcUAeeiM3tId8Stbk4PNtVem/aozNTTa8wFS6', role=3)
user1 = User(username='user1', email='user1@gmail.com', password='$2b$12$JdWTF/r7bfb9ijMoVcUAeeiM3tId8Stbk4PNtVem/aozNTTa8wFS6', role=4)
user2 = User(username='user2', email='user2@gmail.com', password='$2b$12$JdWTF/r7bfb9ijMoVcUAeeiM3tId8Stbk4PNtVem/aozNTTa8wFS6', role=4)
user3 = User(username='bob', email='bob@gmail.com', password='$2b$12$JdWTF/r7bfb9ijMoVcUAeeiM3tId8Stbk4PNtVem/aozNTTa8wFS6', role=4)
user4 = User(username='joe', email='joe@gmail.com', password='$2b$12$JdWTF/r7bfb9ijMoVcUAeeiM3tId8Stbk4PNtVem/aozNTTa8wFS6', role=4)
spc = User(username='spc', email='spc@gmail.com', password='$2b$12$JdWTF/r7bfb9ijMoVcUAeeiM3tId8Stbk4PNtVem/aozNTTa8wFS6', role=5)
db.session.add(gm)
db.session.add(adv)
db.session.add(user1)
db.session.add(user2)
db.session.add(user3)
db.session.add(user4)
db.session.add(spc)
db.session.commit()

Create gm:
gm = User(username='gmaster', email='gmaster@gmail.com', password='$2b$12$MIKYo2NKqRT9nhrKDr4MoeE5SPdEUgboaAziELzc6k2lTU24xuLtC', role=2)
db.session.add(gm)
db.session.commit()

Create adversary:
adv = User(username='adv', email='adv@gmail.com', password='$2b$12$JdWTF/r7bfb9ijMoVcUAeeiM3tId8Stbk4PNtVem/aozNTTa8wFS6', role=3)
db.session.add(adv)
db.session.commit()

Create test users:
user1 = User(username='user1', email='user1@gmail.com', password='$2b$12$JdWTF/r7bfb9ijMoVcUAeeiM3tId8Stbk4PNtVem/aozNTTa8wFS6', role=4)
user2 = User(username='user2', email='user2@gmail.com', password='$2b$12$JdWTF/r7bfb9ijMoVcUAeeiM3tId8Stbk4PNtVem/aozNTTa8wFS6', role=4)
user3 = User(username='bob', email='bob@gmail.com', password='$2b$12$JdWTF/r7bfb9ijMoVcUAeeiM3tId8Stbk4PNtVem/aozNTTa8wFS6', role=4)
user4 = User(username='joe', email='joe@gmail.com', password='$2b$12$JdWTF/r7bfb9ijMoVcUAeeiM3tId8Stbk4PNtVem/aozNTTa8wFS6', role=4)
db.session.add(user1)
db.session.add(user2)
db.session.add(user3)
db.session.add(user4)
db.session.commit()

Create spectator user:
spc = User(username='spc', email='spc@gmail.com', password='$2b$12$JdWTF/r7bfb9ijMoVcUAeeiM3tId8Stbk4PNtVem/aozNTTa8wFS6', role=5)
db.session.add(spc)
db.session.commit()
"""
