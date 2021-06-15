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
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self): #this is what gets printed out for the User
        return f"User('{self.username}','{self.email}')"

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