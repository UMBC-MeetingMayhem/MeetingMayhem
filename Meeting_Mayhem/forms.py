"""
File: forms.py
Author: Robert Shovan /Voitheia
Date: 6/15/2021
E-mail: rshovan1@umbc.edu
Description: python file that handles the registraion and login forms for the website
"""

"""
info about imports
FlaskForm - class we are extending to have our forms
Fields - different types of fields for the website to render
validators - allows the forms to validate different things about the information that is put into them, input sanitization is good
User - import the User class from the models.py file so that we can check if a username or email is already in use
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from Meeting_Mayhem.models import User

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
            raise ValidationError('That username is taken. Please choose a different one.')
    
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