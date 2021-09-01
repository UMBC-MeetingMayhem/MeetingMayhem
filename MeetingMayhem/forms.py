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
import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from wtforms.fields.core import SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from MeetingMayhem.models import Game, User, getAdversaryFactory, getUserFactory, getAllUserFactory, getGameFactory, getAllUserAdversaryFactory
from MeetingMayhem.helper import usernames_to_str_list, parse_for_username

"""
these functions have been moved to the helper.py file, leaving them here for now until playtested properly
#helper functions used in game validation
#recursivley check a string with multiple usernames in it for usernames, and put them in a list
def usernames_to_str_list(usernames, username_list):
    if usernames: #check if usernames is empty or not
        username_list.append(usernames.partition(', ')[0]) #put the first username into the list
        new_usernames = usernames.partition(', ')[2] #grab the rest of the string
        if new_usernames: #if there are still usernames to parse
            username_list = usernames_to_str_list(new_usernames, username_list) #call this method again with the new string
    return username_list #return the list

#recursivley parse the given string for usernames, return a list of usernames delimited by commas
def parse_for_username(str, users):
    if str: #check if the passed string is empty or not
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
"""

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
        if re.compile("[A-Za-z0-9]+").fullmatch(username.data) is None: #check if the username only has letters and numbers, if not, throw an error
            raise ValidationError('Please only use letters and numbers for your username.')
    
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
    recipient = QuerySelectMultipleField(u'Recipient', query_factory=getUserFactory(['id', 'username']), get_label='username', allow_blank=False, validators=[DataRequired()])
    content = StringField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')
    #round, sender should get automatically pulled in the route and send to db item when it is created in the route

#The adversary forms are split up in this way so that it was easier to figure out what the adversary was doing in the routes.py file
#Form for the adversary to create a message. Needed the sender field on top of the other things the Message form has
class AdversaryMessageSendForm(FlaskForm):
    sender = QuerySelectMultipleField(u'Sender', query_factory=getUserFactory(['id', 'username']), get_label='username', validators=[DataRequired()])
    recipient = QuerySelectMultipleField(u'Recipient', query_factory=getUserFactory(['id', 'username']), get_label='username', validators=[DataRequired()])
    content = StringField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')

#Form for the adversary to edit messages
class AdversaryMessageEditForm(FlaskForm):
    new_sender = QuerySelectMultipleField(u'New Sender', query_factory=getUserFactory(['id', 'username']), get_label='username')
    new_recipient = QuerySelectMultipleField(u'New Recipient', query_factory=getUserFactory(['id', 'username']), get_label='username')
    edited_content = StringField('Edited Message')
    submit_edits = SubmitField('Submit Edits')

    def validate_new_sender(self, new_sender):
        if not new_sender.data:
            raise ValidationError('Please select a sender.')
    
    def validate_new_recipient(self, new_recipient):
        if not new_recipient.data:
            raise ValidationError('Please select at least one recipient.')

#Form for the adversary to choose their message to edit or delete message
class AdversaryMessageButtonForm(FlaskForm):
    prev_submit = SubmitField('Previous Message')
    next_submit = SubmitField('Next Message')
    delete_msg = SubmitField('Delete Message')

#Form for the adversary to advance the round
class AdversaryAdvanceRoundForm(FlaskForm):
    advance_round = SubmitField('Advance Round')

#Form for the game master to setup a game
class GMSetupGameForm(FlaskForm):
    name = StringField('Game Name', validators=[DataRequired()])
    adversary = QuerySelectField(u'Adversary', query_factory=getAdversaryFactory(['id', 'username']), get_label='username', validators=[DataRequired()])
    #old players selection field, leaving for now
    #players = QuerySelectMultipleField(u'Players', query_factory=getAllUserFactory(['id', 'username']), get_label='username', validators=[DataRequired()])
    create_game = SubmitField('Create Game')

    def validate_name(self, name):
        # A comment 
        game = Game.query.filter_by(name=name.data).first() #check if there is already a game with the passed name in the db
        if game: #if there is, throw an error
            raise ValidationError('That name is already in use. Please choose a different one.')
    
    def validate_adversary(self, adversary): #check if the adversary is already in a game
        game = Game.query.filter_by(adversary=adversary.data.username, is_running=True).first()
        if game:
            raise ValidationError('That adversary is already in a game. Please choose a different adversary.')

    """ old player validation, leaving for now
    #check if any of the selected players are already in a game
    def validate_players(self, players):
        players_list = [] #generate a string of players for the new game
        players_list = ''.join(map(str, parse_for_username(''.join(map(str, players.data)), players_list)))
        user_list_self = [] #generate a list of players from above string
        user_list_self = usernames_to_str_list(players_list, user_list_self)
        games = Game.query.filter_by(is_running=True).all() #for all of the running games
        for game in games:
            user_list_game = [] #make a list of players in the running games
            user_list_game = usernames_to_str_list(game.players, user_list_game)
            for user_self in user_list_self:
                for user_game in user_list_game:
                    if user_self == user_game: #compare each user in the new game to each user in the running games
                        raise ValidationError('One of the selected users is already in a game.') #if there is a match, raise error
    """

    #check if any of the selected players are already in a game
    #this gets called by the routes.py for validation
    def validate_players_checkbox(players):
        user_list_self = [] #generate a list of players from above string
        user_list_self = usernames_to_str_list(players, user_list_self)
        if len(user_list_self) > 4:
            raise ValidationError('Each game session can only have a maximum of 4 players.')
        else:
            games = Game.query.filter_by(is_running=True).all() #for all of the running games
            for game in games:
                user_list_game = [] #make a list of players in the running games
                user_list_game = usernames_to_str_list(game.players, user_list_game)
                for user_self in user_list_self:
                    for user_game in user_list_game:
                        if user_self == user_game: #compare each user in the new game to each user in the running games
                            raise ValidationError('One of the selected users is already in a game.') #if there is a match, raise error

#Form for the game master to end a game
class GMManageGameForm(FlaskForm):
    games = QuerySelectMultipleField(u'Games', query_factory=getGameFactory(['id', 'name']), get_label='name', validators=[DataRequired()])
    end_game = SubmitField('End Game')

#Form for the game master to manage the role of users
class GMManageUserForm(FlaskForm):
    user = QuerySelectField(u'User', query_factory=getAllUserAdversaryFactory(['id', 'username']), get_label='username', validators=[DataRequired()])
    role = SelectField(u'Role', choices=[('adv', 'Adversary'), ('usr', 'User')], validators=[DataRequired()])
    update = SubmitField('Update User')