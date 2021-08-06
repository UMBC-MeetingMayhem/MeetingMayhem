"""
File: forms.py
Author: Robert Shovan /Voitheia
Date Created: 6/15/2021
Last Modified: 7/21/2021
E-mail: rshovan1@umbc.edu
Description: python file that handles the registraion and login forms for the website
"""

"""
info about imports
FlaskForm - class we are extending to have our forms
Fields - different types of fields for the website to render
validators - allows the forms to validate different things about the information that is put into them, input sanitization is good
User - import the User class from the models.py file so that we can check if a username or email is already in use
getUserFactory - used to pull the usernames for the recipient selection
"""
from re import U
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from wtforms.fields.core import SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from MeetingMayhem.models import Game, User, getAdversaryFactory, getUserFactory, getAllUserFactory, getGameFactory, getAllUserAdversaryFactory

def usernames_to_str_list(usernames, username_list):
    #print('start')
    #print(usernames)
    #print(username_list)
    username_list.append(usernames.partition(', ')[0])
    new_usernames = usernames.partition(', ')[2]
    #print(new_usernames)
    #print(username_list)
    if new_usernames:
        username_list = usernames_to_str_list(new_usernames, username_list)
        #print(username_list)
        #print('if')
    return username_list

#recursivley parse the given string for usernames, return a list of usernames delimited by commas
def parse_for_username(str, users):
    #print(str)
    str1=str.partition("Username='")[2] #grabs all the stuff in the string after the text "Username='"
    str2=str1.partition("', ") #separates the remaining string into the username, the "', ", and the rest of the string
    if str2[2]: #if there is content in the rest of the string
        if (str2[2].find('Username') != -1): #if we can find the text 'Username' in the rest of the string
            user = str2[0] + ', ' #put a comma and space after the username
            users.append(user) #append it to the list
            parse_for_username(str2[2], users) #call this method again
        else: #if not
            users.append(str2[0]) #just append the username as it is the last one
    return users #return the list of usernames

#this part handles the registraion form for new users
#i feel like these fields and variables are pretty self-explanatory, the first string passed is the title of the field
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first() #check if there is already a user with the passed username in the db
        if user: #if there is, throw an error
            raise ValidationError('That username is already in use. Please choose a different one.')
    
    def validate_email(self, email):
        email = User.query.filter_by(email=email.data).first() #check if there is already a user with the passed email in the db
        if email: #if there is, throw an error
            raise ValidationError('That email is already in use. Please choose a different one.')

#this part handles the login form for existing users to log into the website
#i feel like these fields and variables are pretty self-explanatory, the first string passed is the title of the field
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

#Message form for users to construct messages with
class MessageForm(FlaskForm):
    #the whole query_factory thing is responsible for pulling the users to select for the dropdown
    recipient = QuerySelectMultipleField(u'Recipient', query_factory=getUserFactory(['id', 'username']), get_label='username', allow_blank=False)
    content = StringField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')
    #round, sender should get automatically pulled in the route and send to db item when it is created in the route

#The adversary forms are split up in this way so that it was easier to figure out what the adversary was doing in the routes.py file
#Form for the adversary to create a message. Needed the sender field on top of the other things the Message form has
class AdversaryMessageSendForm(FlaskForm):
    sender = QuerySelectMultipleField(u'Sender', query_factory=getUserFactory(['id', 'username']), get_label='username')
    recipient = QuerySelectMultipleField(u'Recipient', query_factory=getUserFactory(['id', 'username']), get_label='username')
    content = StringField('Message')
    submit = SubmitField('Send Message')

#Form for the adversary to edit messages
class AdversaryMessageEditForm(FlaskForm):
    new_sender = QuerySelectMultipleField(u'New Sender', query_factory=getUserFactory(['id', 'username']), get_label='username')
    new_recipient = QuerySelectMultipleField(u'New Recipient', query_factory=getUserFactory(['id', 'username']), get_label='username')
    edited_content = StringField('Edited Message')
    submit_edits = SubmitField('Submit Edits')

#Form for the adversary to choose their message to edit or delete message
class AdversaryMessageButtonForm(FlaskForm):
    prev_submit = SubmitField('Previous Message')
    next_submit = SubmitField('Next Message')
    delete_msg = SubmitField('Delete Message')

#Form for the adversary to advance the round
class AdversaryAdvanceRoundForm(FlaskForm):
    advance_round = SubmitField('Advance Round')

class GMSetupGameForm(FlaskForm):
    name = StringField('Game Name')
    adversary = QuerySelectField(u'Adversary', query_factory=getAdversaryFactory(['id', 'username']), get_label='username')
    players = QuerySelectMultipleField(u'Players', query_factory=getAllUserFactory(['id', 'username']), get_label='username')
    create_game = SubmitField('Create Game')

    def validate_name(self, name):
        game = Game.query.filter_by(name=name.data).first() #check if there is already a user with the passed username in the db
        if game: #if there is, throw an error
            raise ValidationError('That name is already in use. Please choose a different one.')
    
    def validate_players(self, players):
        players_list = []
        players_list = ''.join(map(str, parse_for_username(''.join(map(str, players.data)), players_list)))
        user_list_self = []
        user_list_self = usernames_to_str_list(players_list, user_list_self)
        games = Game.query.filter_by(is_running=True).all()
        for game in games:
            user_list_game = []
            user_list_game = usernames_to_str_list(game.players, user_list_game)
            for user_self in user_list_self:
                for user_game in user_list_game:
                    if user_self == user_game:
                        raise ValidationError('One of the selected users is already in a game.')

class GMManageGameForm(FlaskForm):
    games = QuerySelectMultipleField(u'Games', query_factory=getGameFactory(['id', 'name']), get_label='name')
    end_game = SubmitField('End Game')

class GMManageUserForm(FlaskForm):
    user = QuerySelectField(u'User', query_factory=getAllUserAdversaryFactory(['id', 'username']), get_label='username')
    role = SelectField(u'Role', choices=[('adv', 'Adversary'), ('usr', 'User')])
    update = SubmitField('Update User')