"""
File: models.py
Author: Robert Shovan /Voitheia
Date: 6/15/2021
E-mail: rshovan1@umbc.edu
Description: python file that handles the database
"""

"""
info about imports
db, login_manager - import from __init__.py the database and login manager so we can put users in the database and do login stuff
UserMixin - does some magic so that handling user login is easy
"""
from Meeting_Mayhem import db, login_manager
from flask_login import UserMixin

#login management

@login_manager.user_loader #tells login manager that this is the user loader function
def load_user(user_id):
    return User.query.get(int(user_id))

#this is basically creating the tables for the database
#i feel like fields and variables are pretty self explanatory here
#user table
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    #packets = db.relationship('Packet', backref='sender', lazy=True) #the backref allows the posts to reference the users without needing a column in the posts table, not sure if this will work properly
    #role = db.Column(db.Integer, nullable=False) #contains if the user is a player or adversary, also GM later

    def __repr__(self): #this is what gets printed out for the User
        return f"User('{self.username}','{self.email}')"

"""
#added this part 6/16/21
#packet table
#the intent is to have the round get passed from routes.py, as I think that is a good place to keep track of it
#sender and recipient should get pulled from the current user and a dropdown respectivley
#content gets pulled should get pulled from a text box
#later, a packet will need a boolean to indicate if the packet has been edited by the adversary or not
#the packet will also need an "edited_content" field
class Packet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    round = db.Column(db.Integer, nullable=False)
    sender = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    def __repr__(self):
        return f"Packet('{self.round}','{self.sender}','{self.recipient}','{self.content}'"
"""

#--------------------info about database stuff with python--------------------#
# this section should probably be moved to not here 
#run python
#from <filename> import db (ex: from Meeting_Mayhem import db)
#from <filename> import User (ex: from Meeting_Mayhem import User)
#-these imports allow us to use the classes and db on the python command line
#db.create_all()
#-creates all the tables needed for the db
#user_1 = User(username='bob', email='bob@gmail.com', password='password')
#-this creates a user variable
#db.session.add(user_1)
#-this adds the user we created to the "stack" that is waiting to be committed to the db
#user_2 = User(username='joe', email='joe@gmail.com', password='password')
#db.session.add(user_2)
#db.session.commit()
#-commits the users we added to the "stack" to the db
#User.query.all()
#-querys the database for all users
#User.query.first()
#-gets the first user
#User.query.filter_by(username='bob').all()
#-querys the database for all users with username of 'bob'
#user = User.query.filter_by(username='bob').first()
#-puts the bob user into a variable of "user"
#user
#-will print out the information of the user in the user variable
#user.id
#-will print out the id of the user in the user variable
#user = User.query.get(2)
#-sets the user variable to the user of id 2
#post_1 = Post(title='thingy', content='this has stuff in it yeee', user_id=user.id)
#-makes a new post variable with information in it that has an author of the user variable
#db.drop_all()
#-drops all tables