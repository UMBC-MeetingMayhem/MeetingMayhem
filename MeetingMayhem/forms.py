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
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, HiddenField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from wtforms.fields.core import SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from MeetingMayhem.models import Game, User, getAdversaryFactory, getGameFactory, getNonGMUsersFactory
from MeetingMayhem.helper import str_to_list

#this part handles the registraion form for new users
#i feel like these fields and variables are pretty self-explanatory, the first string passed is the title of the field
class RegistrationForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
	selected_image = HiddenField('Selected Image')
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


#Message form for users and adversary to construct messages with
class MessageForm(FlaskForm):
	content = StringField('', validators=[DataRequired()])
	submit = SubmitField('Send Message')
	encryption_and_signed_keys = StringField('Key(s)')
	#round, sender should get automatically pulled in the route and send to db item when it is created in the route
	meet_location = SelectField('locations', choices=["Locations", "Cafe", "Track", "Alley", "Dorm", "Garage", "Lab", "Park"])
	meet_time = SelectField('time', choices=["Time", "1:00", "2:00", "3:00", "4:00", "5:00", "6:00", "7:00", "8:00", "9:00", "10:00", "11:00", "12:00"])
	meet_am_pm = SelectField('am_pm', choices=["am", "pm"], default="am")
	encryption_type = SelectField('encryption_sign_type_select', choices=["No Encryption/Signature", "Symmetrically Encrypt", "Asymmetrically Encrypt","Sign"], default="No Encryption/Signature")
	def validate_encryption_and_signed_keys(self, encryption_and_signed_keys):
		keys = (encryption_and_signed_keys.data).lower().split(',')
		if encryption_and_signed_keys.data == '':
			return
		for element in keys:
			if (not(bool(re.match("signed[(][a-zA-Z0-9]+[.](private|public)[)]$", element))) and not(bool(re.match("symmetric[(][a-zA-Z0-9]+[.](private|public|key pair)[)]$", element))) and not(bool(re.match("asymmetric[(][a-zA-Z0-9]+[.](private|public)[)]$", element)))):
				raise ValidationError("Enter in following format Signed/Encrypted(username.private/public),Sign/Encrypt(username.private/public),....etc")

#Form for the adversary to edit messages
class AdversaryMessageEditForm(FlaskForm):
	edited_content = StringField('Edited Message')
	meet_location = SelectField('locations', choices=["Locations", "Cafe", "Track", "Alley", "Dorm", "Garage", "Lab", "Park"])
	meet_time = SelectField('time', choices=["Time", "1:00", "2:00", "3:00", "4:00", "5:00", "6:00", "7:00", "8:00", "9:00", "10:00", "11:00", "12:00"])
	meet_am_pm = SelectField('am_pm', choices=["am", "pm"], default="am")
	msg_num = IntegerField()
	submit_edits = SubmitField('Forward Message')
	send_no_change = SubmitField('Forward Message (no changes)')
	delete_msg = SubmitField('Delete Message')
	encryption_and_signed_keys = StringField('Key(s)')
	not_editable = BooleanField()

	def validate_encryption_and_signed_keys(self, encryption_and_signed_keys):
		keys = (encryption_and_signed_keys.data).lower().split(',')
		if encryption_and_signed_keys.data == '':
			return
		for element in keys:
			if (not(bool(re.match("signed[(][a-zA-Z0-9]+[.](private|public)[)]$", element))) and not(bool(re.match("symmetric[(][a-zA-Z0-9]+[.](private|public|shared)[)]$", element))) and not(bool(re.match("asymmetric[(][a-zA-Z0-9]+[.](private|public)[)]$", element)))):
				raise ValidationError("Enter in following format Signed/Encrypted(username.private/public),Sign/Encrypt(username.private/public),....etc")

#Form for the adversary to advance the round
class AdversaryAdvanceRoundForm(FlaskForm):
	advance_round = SubmitField('Advance Round')

#Form for the game master to setup a game
class GMSetupGameForm(FlaskForm):
	name = StringField('Game Name', validators=[DataRequired()])
	adversary = QuerySelectField(u'Adversary', query_factory=getAdversaryFactory(['id', 'username']), get_label='username', validators=[DataRequired()])
	create_game = SubmitField('Create Game')


	def validate_name(self, name):
		game = Game.query.filter_by(name=name.data).first() #check if there is already a game with the passed name in the db
		if game: #if there is, throw an error
			raise ValidationError('That name is already in use. Please choose a different one.')

	def validate_adversary(self, adversary): #check if the adversary is already in a game
		game = Game.query.filter_by(adversary=adversary.data.username, is_running=True).first()
		if game:
			raise ValidationError('That adversary is already in a game. Please choose a different adversary.')

	#check if any of the selected players are already in a game
	#this gets called by the routes.py for validation
	def validate_players_checkbox(players):
		user_list_self = [] #generate a list of players from above string
		user_list_self = str_to_list(players, user_list_self)
		if len(user_list_self) > 4:
			raise ValidationError('Each game session can only have a maximum of 4 players.')
		else:
			games = Game.query.filter_by(is_running=True).all() #for all of the running games
			for game in games:
				user_list_game = [] #make a list of players in the running games
				user_list_game = str_to_list(game.players, user_list_game)
				for user_self in user_list_self:
					for user_game in user_list_game:
						if user_self == user_game: #compare each user in the new game to each user in the running games
							raise ValidationError('One of the selected users is already in a game.') #if there is a match, raise error

#Form for the game master to end a game
class GMManageGameForm(FlaskForm):
	game = QuerySelectField(u'Games', query_factory=getGameFactory(['id', 'name']), get_label='name', validators=[DataRequired()])
	end_game = SubmitField('End Game') #ends the game completely
	end_game_page = SubmitField('End Game Page') #brings the game to the end of game page, used for testing
	random = SubmitField('Randomize the adv')

#Form for the game master to manage the role of users
class GMManageUserForm(FlaskForm):
	user = QuerySelectField(u'User', query_factory=getNonGMUsersFactory(['id', 'username']), get_label='username', validators=[DataRequired()])
	role = SelectField(u'Role', choices=[('adv', 'Adversary'), ('usr', 'User'), ('spec', 'Spectator'), ('inac', 'Inactive')], validators=[DataRequired()])
	profile = SelectField(u'Role', choices=[('/images/Arts/Characters/1-Jordan/1-Jordan_Profile.png', 'Jordan'), ('/images/Arts/Characters/2-Dakota/2-Dakota_Profile.png', 'Dakota'), ('/images/Arts/Characters/3-Yasmin/3-Yasmin_Profile.png', 'Yasmin'), ('/images/Arts/Characters/4-Derek/4-Derek_Profile.png', 'Derek'),('/images/Arts/Characters/5-Kaede/5-Kaede_Profile.png','Kaede'),('/images/Arts/Characters/6-Manuel/6-Manuel_Profile.png','Manuel'),('/images/Arts/Characters/7-Spy/7-Spy_Profile.png','Spy'),('/images/Arts/Characters/8-Spyess/8-Spyess_Profile.png','Spyess'),('/images/Arts/Characters/9-Kody/9-Kody_Profile.png','Kody')], validators=[DataRequired()])
	update = SubmitField('Update User')
	update_profile  = SubmitField('Update Profile')

# Form for a user to select a game
class GameSelectForm(FlaskForm):
	running_games = QuerySelectField(u'Game', query_factory=getGameFactory(['id', 'name']), get_label='name', validators=[DataRequired()])
	select_game = SubmitField('Select Game')

# Form for game master to get game info
#class GMSelectForm(FlaskForm):
#running_games = QuerySelectField(u'Game', query_factory=getGameFactory(['id', 'name']), get_label='name', validators=[DataRequired()])
#select_game = SubmitField('Select Game')