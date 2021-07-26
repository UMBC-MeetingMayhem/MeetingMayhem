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
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.ext.sqlalchemy.fields import QuerySelectField, QuerySelectMultipleField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from MeetingMayhem.models import User, getUserFactory

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
    #recipient = QuerySelectField(u'Recipient', query_factory=getUserFactory(['id', 'username']), get_label='username', allow_blank=False)
    recipient = QuerySelectMultipleField(u'Recipient', query_factory=getUserFactory(['id', 'username']), get_label='username', allow_blank=False)
    content = StringField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')
    #round, sender should get automatically pulled in the route and send to db item when it is created in the route

#The adversary forms are split up in this way so that it was easier to figure out what the adversary was doing in the routes.py file
#Form for the adversary to create a message. Needed the sender field on top of the other things the Message form has
class AdversaryMessageSendForm(FlaskForm):
    #sender = QuerySelectField(u'Sender', query_factory=getUserFactory(['id', 'username']), get_label='username')
    #recipient = QuerySelectField(u'Recipient', query_factory=getUserFactory(['id', 'username']), get_label='username')
    sender = QuerySelectMultipleField(u'Sender', query_factory=getUserFactory(['id', 'username']), get_label='username')
    recipient = QuerySelectMultipleField(u'Recipient', query_factory=getUserFactory(['id', 'username']), get_label='username')
    content = StringField('Message')
    submit = SubmitField('Send Message')

#Form for the adversary to edit messages
class AdversaryMessageEditForm(FlaskForm):
    #new_sender = QuerySelectField(u'New Sender', query_factory=getUserFactory(['id', 'username']), get_label='username')
    #new_recipient = QuerySelectField(u'New Recipient', query_factory=getUserFactory(['id', 'username']), get_label='username')
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