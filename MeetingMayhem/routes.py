"""
File: routes.py
Author: Robert Shovan /Voitheia
Date Created: 6/15/2021
Last Modified: 7/14/2021
E-mail: rshovan1@umbc.edu
Description: python file that handles the routes for the website.
"""

"""
info about imports
render_template - used for giving the website the final html page with the layout and passed page
url_for - used to resolve the url for the passed string
flash - used for alerts sent to the user
redirect - used to redirect the user to a different page when something happens
request - variable that contains the requests made by the website users
app, db, bcrypt - import the app, database, and encryption functionality from the package we initialized in the __init__.py file
forms - import the forms we created in the forms.py file so we can send them to the html templates
models - imports the models created in models.py so that we can create new db items, query the db, and update db items
flask_login - different utilities used for loggin the user in, seeing which user is logged in, logging the user out, and requireing login for a page
"""
from flask_socketio import send, emit, join_room, leave_room
from flask import render_template, url_for, flash, redirect, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from wtforms.validators import ValidationError
from MeetingMayhem import app, db, bcrypt, socketio
from MeetingMayhem.forms import GMManageUserForm, RegistrationForm, LoginForm, MessageForm, AdversaryMessageEditForm, AdversaryAdvanceRoundForm, GMManageGameForm, GMSetupGameForm, GameSelectForm
from MeetingMayhem.models import User, Message, Game
from MeetingMayhem.helper import check_for_str, strip_list_str, str_to_list, create_message, can_decrypt
from datetime import datetime 
from collections import Counter

import pytz

#root route, basically the homepage, this page doesn't really do anything right now
#having two routes means that flask will put the same html on both of those pages
#by using the render_template, we are able to pass an html document to flask for it to put on the web server
@app.route('/') #this line states that if the user tries to access http:/<IP>:5000/ it will use the home funciton
@app.route('/home') #likewise, this line is for http:/<IP>:5000/home
def home():
	if current_user.is_anonymous: #ask the user to login or register if they aren't logged in
		flash(f'Please register for an account or login to proceed.', 'info')
	elif not current_user.game and (current_user.role == 3 or current_user.role == 4): #if the user is logged in but isn't in a game, display below message
		flash(f'You are not currently in a game. Please have your game master create a game to proceed.', 'info')
	return render_template('home.html', title='Home') #this line passes the template we want to use and any variables it needs to it

#about page route, this page doesn't really do anything right now
@app.route('/about')
def about():
	return render_template('about.html', title='About')

#registration page route
@app.route('/register', methods=['GET', 'POST']) #POST is enabled here so that users can give the website information to register with
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home')) #if the user is logged in, redir to home
	form = RegistrationForm() #specify which form to use
	if form.validate_on_submit(): #when the submit button is pressed on the form
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8') #this hashes the user's password and converts it to utf-8
		user = User(username=form.username.data, email=form.email.data, password=hashed_password, role='4') #create the user for the db
		db.session.add(user) #stage the user for the db
		db.session.commit() #commit new user to db
		flash(f'Your account has been created! Please login.', 'success') #flash a success message to let the user know the account was made
		
		socketio.emit('new_player',broadcast=True)
		
		return redirect(url_for('login')) #redir the user to the login page
	return render_template('register.html', title='Register', form=form)

#login page route
@app.route('/login', methods=['GET', 'POST']) #POST is enabled here so that users can give the website information to login with
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home')) #if the user is logged in, redir to home
	form = LoginForm() #specify which form to use
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first() #check that the user exists, using username because that's what the user uses to log in
		if user and bcrypt.check_password_hash(user.password, form.password.data): #if the user exists and the password is correct
			login_user(user, remember=form.remember.data) #log the user in, and if the user checked the remeber box, remember the user (not sure if remember actually works)
			next_page = request.args.get('next') #check if the next argument exists (i.e. user tried to go somewhere they needed to login to see)
			flash(f'You are now logged in!', 'success') #notify the user they are logged in
			return redirect(next_page) if next_page else redirect(url_for('home')) #redir the user to the next_page arg if it exists, if not send them to home page
		else:
			flash(f'Login Unsuccessful. Please check username and password.', 'danger') #display error message
	return render_template('login.html', title='Login', form=form)

#logout route
@app.route('/logout')
def logout():
	logout_user() #logout user
	flash(f'You have been logged out.', 'success') #notify the user that they have been logged out
	return redirect(url_for('home')) #redir the user to the home page

#account page route, this page has the user's username and areas for stats and account information when that gets implemented
@app.route('/account', methods=['GET', 'POST']) #, methods=['GET', 'POST']) needs to be removed when the decrement round button is
@login_required #enforces that the the user needs to be logged in if they navigate to this page
def account():
	#create a button in the account page that can decrement the round for testing purposes, will only be displayed for adversary user
	form = AdversaryAdvanceRoundForm()
	current_game = Game.query.filter_by(adversary=current_user.username, is_running=True).first()
	if form.advance_round.data and current_game:
		current_game.current_round -= 1
		current_game.adv_current_msg = 0
		current_game.adv_current_msg_list_size = 0
		db.session.commit()
	return render_template('account.html', title='Account', form=form)

#message page
#TODO: check for duplicate post request when sending messages
@app.route('/messages', methods=['GET', 'POST']) #POST is enabled here so that users can give the website information to create messages with
@login_required
def messages():

	#if the current user isn't in a game, send them to the homepage and display message
	if not current_user.game:
		flash(f'You are not currently in a game. Please have your game master put you in a game.', 'danger')
		return render_template('home.html', title='Home')

	#set the display_message to None initially so that if there is no message to display it doesn't break the website
	display_message = None

	# -----------------------------------------------------------------------------------------------------------
	#if the current_user is of adversary role, then display the adversary version of the page 
	if (current_user.role==3):
		return adv_messages_page()
		
	# -----------------------------------------------------------------------------------------------------------
	#for regular users

	#setup the current_game variable so we can pull information from it
	game_id = None
	games = Game.query.filter_by(is_running=True).all() #grab all the running games
	for game in games:
		if check_for_str(game.players, current_user.username): #check if the current_user is in the target game
			game_id = game.id #if they are, set the game_id variable to the found game

	current_game = Game.query.filter_by(id=game_id).first() #select the current_game by id

	#create list of usernames for checkboxes
	users = User.query.filter_by(role=4, game=current_game.id).all()
	usernames = []
	for user in users:
		usernames.append(user.username)

	form = MessageForm() #use the standard message form
	#msgs = None
	msgs_tuple = []
	if (current_game.current_round>=1):
		#pull messages from current_round where the message isn't deleted
		display_message = Message.query.filter_by(adv_submitted=True, is_deleted=False, game=current_game.id).all()
		#msgs = [] #create a list to store the messages to dispay to pass to the template
		for message in display_message: #for each message
			if (message.is_edited and check_for_str(message.new_recipient, current_user.username)) or ((not message.is_edited) and check_for_str(message.recipient, current_user.username)):
				message.time_recieved = datetime.now(pytz.timezone("US/Eastern")).strftime("%b.%d.%Y-%H.%M")
				msgs_tuple.append((message, can_decrypt(current_user, message.encryption_details, message.is_encrypted, message.sender)))
				db.session.commit()

	#setup message flag to tell template if it should display messages or not
	#msg_flag = True
	#if not msgs_tuple: #if the list of messages is empty, set the flag to false
	#	msg_flag = False

	msg_flag = False
	if msgs_tuple:
		msg_flag = True
		msgs_tuple.reverse()
		
	#sent messages
	sent_msgs = Message.query.filter_by(sender=current_user.username, game=current_game.id).all()
	sent_msgs.reverse()
	
	if form.validate_on_submit(): #when the user submits the message form and it is valid

		#capture the list of players from the checkboxes and make it into a string delimited by commas
		checkbox_output_list = request.form.getlist('recipients')
		

		#ensure the list isn't empty
		if not checkbox_output_list:
			flash(f'Please select at least one recipient.', 'danger')
			return render_template('messages.html', title='Messages', form=form, msgs=msgs_tuple, game=current_game, msg_flag=msg_flag, sent_msgs=sent_msgs, usernames=usernames)
		
		#ensure keys entered are keys of actual recipients chosen
		curr_time = datetime.now(pytz.timezone("US/Eastern")).strftime("%b.%d.%Y-%H.%M")
		create_message(current_user, current_game, request.form, form, current_user.username, curr_time)
		update()
		
	#sent messages
	sent_msgs = Message.query.filter_by(sender=current_user.username, game=current_game.id).all()
	sent_msgs.reverse()
	
	#give the template the vars it needs
	return render_template('messages.html', title='Messages', form=form, msgs=msgs_tuple, game=current_game, msg_flag=msg_flag, sent_msgs=sent_msgs, usernames=usernames)

def adv_messages_page():
		#setup the current_game so that we can pull information from it
		current_game = Game.query.filter_by(adversary=current_user.username, is_running=True).first()

		#setup variables for the forms the adversary needs to use
		msg_form = MessageForm()
		adv_msg_edit_form = AdversaryMessageEditForm()
		adv_next_round_form = AdversaryAdvanceRoundForm()

		#setup variable to contain the messages that are in the current_round of this game
		messages = Message.query.filter_by(adv_submitted=False, adv_created=False, game=current_game.id).all()
		msgs_tuple = []
		for element in messages:
			msgs_tuple.append((element, can_decrypt(current_user, element.encryption_details, element.is_encrypted, element.sender)))
		#create list of usernames for checkboxes
		users = User.query.filter_by(role=4, game=current_game.id).all()
		usernames = []
		for user in users:
			usernames.append(user.username)


		#grab the messages from previous rounds, this is done here because the previous messages shouldn't change

		prev_msgs_tuple = []
	
		prev_messages = Message.query.filter_by(game=current_game.id, adv_submitted=True).all() #grab all the previous messages for this game
		
		for message in prev_messages:
			prev_msgs_tuple.append((message, can_decrypt(current_user, message.encryption_details, message.is_encrypted,message.sender))) # append it to the tuple 
			
			# the message.sender may cause a bug im not sure.
		
		prev_msgs_tuple.reverse()
		
		#make a flag that the template uses to determine if it should display previous messages or not
		prev_msg_flag = True
		if not prev_msgs_tuple: #if the list of previous messages is empty, set the flag to false
			prev_msg_flag = False


		if messages: #if messages has content, set the display message to the adversary's current message
			display_message = messages[current_game.adv_current_msg]

		else: #if there are no messages, set display message to none
			display_message = None

		if display_message != None:
			can_decrypt_curr_message = can_decrypt(current_user, display_message.encryption_details, display_message.is_encrypted, display_message.sender)
		else:
			can_decrypt_curr_message = 1
		#set the adv_current_msg_list_size so that the edit message box "scrolling" works correctly
		current_game.adv_current_msg_list_size = len(messages)

		#create variables for the edit message box buttons so that we only check their state once
		is_submit_edits = adv_msg_edit_form.submit_edits.data
		is_delete_msg = adv_msg_edit_form.delete_msg.data
		is_send_no_change = adv_msg_edit_form.send_no_change.data
		
		#adversary message creation
		if msg_form.submit.data and msg_form.validate(): #if the adversary tries to send a message, and it is valid

			curr_time = datetime.now(pytz.timezone("US/Eastern")).strftime("%b.%d.%Y-%H.%M")
			create_message(current_user, current_game, request.form, msg_form, current_user.username, curr_time)

			#pull the messages again since the messages we want to display has changed
			messages = Message.query.filter_by(adv_submitted=False, adv_created=False, game=current_game.id).all()
			msgs_tuple = []
			for element in messages:
				
				msgs_tuple.append((element, can_decrypt(current_user, element.encryption_details, element.is_encrypted, element.sender)))
		

			current_game.adv_current_msg = 0
			current_game.adv_current_msg_list_size = len(messages)
			#commit the messages to the database
			db.session.commit()
			update()
			# #render the webpage
			return render_template('adversary_messages.html', title='Messages', msg_form=msg_form, adv_msg_edit_form=adv_msg_edit_form,
			adv_next_round_form=adv_next_round_form, message=display_message, can_decrypt = can_decrypt_curr_message, game=current_game,
			current_msg=(current_game.adv_current_msg+1), msg_list_size=current_game.adv_current_msg_list_size, prev_msgs=prev_msgs_tuple, prev_msg_flag=0, usernames=usernames, msgs=msgs_tuple)


		#adversary message editing
		elif (is_submit_edits or is_delete_msg or is_send_no_change): #if any of the prev/next/submit buttons are clicked
			display_message = Message.query.filter_by(id=adv_msg_edit_form.msg_num.data).first()
			
			if display_message != None:
				can_decrypt_curr_message = can_decrypt(current_user, display_message.encryption_details, display_message.is_encrypted, display_message.sender)
			else:
				can_decrypt_curr_message = 1
			
			#TODO: some sort of validation here? - not sure if needed cause users are chosen from dropdown/checkboxes
			if is_submit_edits and adv_msg_edit_form.validate(): #if the submit button is clicked

				#capture the list of players from the checkboxes and make it into a string delimited by commas
				checkbox_output_list_new_recipients = request.form.getlist('new_recipients')
				checkbox_output_list_new_senders = request.form.getlist('new_senders')

				#ensure the lists aren't empty
				if not checkbox_output_list_new_recipients or not checkbox_output_list_new_senders:
					flash(f'Please select at least one sender and one recipient.', 'danger')
					return render_template('adversary_messages.html', title='Messages', msg_form=msg_form, adv_msg_edit_form=adv_msg_edit_form,
					adv_next_round_form=adv_next_round_form, message=display_message, can_decrypt = can_decrypt_curr_message, game=current_game,
					current_msg=(current_game.adv_current_msg+1), msg_list_size=current_game.adv_current_msg_list_size, prev_msgs=prev_msgs_tuple, prev_msg_flag=0, usernames=usernames, msgs=msgs_tuple)

				checkbox_output_str_new_recipients = ''.join(map(str, checkbox_output_list_new_recipients))
				checkbox_output_str_new_senders = ''.join(map(str, checkbox_output_list_new_senders))
				new_recipients = checkbox_output_str_new_recipients[:len(checkbox_output_str_new_recipients)-2]
				new_senders = checkbox_output_str_new_senders[:len(checkbox_output_str_new_senders)-2]
				new_keys = request.form.get('encryption_and_signed_keys')
			
				signed_keys = [] # list to keep track of digital signatures
				encrypted_keys = [] # list to keep track of encryption keys

				dict_of_recipients = {} # Dictionary to allow for quick look up times when seeing if recipient among encryption/sign keys
				dict_of_senders = {} # Dictionary to allow for quick look up times when seeing if sender among encryption/sign keys

				# Code to remove wierd commas from get request 
				for i in range(len(checkbox_output_list_new_recipients)):
					checkbox_output_list_new_recipients[i] = checkbox_output_list_new_recipients[i].split(',')[0]

				for i in range(len(checkbox_output_list_new_senders)):
					checkbox_output_list_new_senders[i] = checkbox_output_list_new_senders[i].split(',')[0]

				for element in checkbox_output_list_new_recipients: #populates dict with recipients chosen
					dict_of_recipients[element] = 0

				for element in checkbox_output_list_new_senders: #populates dict with recipients chosen
					dict_of_senders[element] = 0

				# Code for determining whether entered keys are valid or not
				for element in new_keys.split(','):
					if element.split('(')[0].lower() == 'sign':
						if element.split('(')[1] == f"{current_user.username}.priv)":
							signed_keys.append(element.split('(')[1][0:len(element.split('(')[1]) - 1])
						else:
							signed_keys.append('invalid sign key')
					if element.split('(')[0].lower() == 'encrypt':
						if (element.split('.')[0].split('(')[1] in dict_of_recipients or element.split('.')[0].split('(')[1] in dict_of_senders) and (element.split('.')[1] == 'pub)' or element.split('(')[1] == f"{current_user.username}.priv)"):
							encrypted_keys.append(element.split('(')[1][0:len(element.split('(')[1]) - 1])
						else:
							encrypted_keys.append('invalid encrypted key')

				signed_keys_string = ", ".join(map(str, signed_keys))
				encrypted_keys_string = ", ".join(map(str, encrypted_keys))

				#setup the changes to be made to the current message 
				display_message.is_signed = False
				display_message.signed_details = ""
				display_message.is_encrypted = False 
				display_message.encryption_details = ""
				display_message.is_edited = True
				display_message.new_sender = new_senders
				display_message.new_recipient = new_recipients
				display_message.edited_content = adv_msg_edit_form.edited_content.data

				if len(signed_keys) > 0:
					display_message.is_signed = True 
					display_message.signed_details = signed_keys_string
				if len(encrypted_keys) > 0:
					display_message.is_encrypted = True 
					display_message.encryption_details = encrypted_keys_string
					
				#pull the messages again since the messages we want to display has changed
				messages = Message.query.filter_by(adv_submitted=False, adv_created=False, game=current_game.id).all()
				msgs_tuple = []
				for element in messages:
					msgs_tuple.append((element, can_decrypt(current_user, element.encryption_details, element.is_encrypted, element.sender)))
				#current_game.adv_current_msg = 0
				#current_game.adv_current_msg_list_size = len(messages)
				#commit the messages to the database
				display_message.adv_submitted = True
				messages = Message.query.filter_by(adv_submitted=False, adv_created=False, game=current_game.id).all()
				msgs_tuple = []
				for element in messages:
					msgs_tuple.append((element, can_decrypt(current_user, element.encryption_details, element.is_encrypted, element.sender)))
				db.session.commit()

			elif is_delete_msg: #if the delete message button is clicked
				#flag the message as edited and deleted
				display_message.adv_submitted = True 
				display_message.is_edited = True
				display_message.is_deleted = True
				db.session.commit()
				#pull the messages again since the messages we want to display has changed
				messages = Message.query.filter_by(adv_submitted=False, adv_created=False, game=current_game.id).all()
				msgs_tuple = []
				for element in messages:
					msgs_tuple.append((element, can_decrypt(current_user, element.encryption_details, element.is_encrypted, element.sender)))
				#current_game.adv_current_msg = 0
				#current_game.adv_current_msg_list_size = len(messages)
				#commit the messages to the database
				db.session.commit()

			elif is_send_no_change:
				#flash(display_message.content)
				display_message.adv_submitted = True 
				db.session.commit()
				messages = Message.query.filter_by(adv_submitted=False, adv_created=False, game=current_game.id).all()
				msgs_tuple = []
				for element in messages:
					msgs_tuple.append((element, can_decrypt(current_user, element.encryption_details, element.is_encrypted, element.sender)))
				#current_game.adv_current_msg = 0
				#current_game.adv_current_msg_list_size = len(messages)
				#commit the messages to the database
				db.session.commit()

			is_submit_edits = False
			is_delete_msg = False
			is_send_no_change = False 

			prev_messages = Message.query.filter_by(game=current_game.id, adv_submitted=True).all() #grab all the previous messages for this game
		
			for message in prev_messages:
				prev_msgs_tuple.append((message, can_decrypt(current_user, message.encryption_details, message.is_encrypted,message.sender))) # append it to the tuple 

			prev_msgs_tuple.reverse()
			#render the webpage

			update()
			return render_template('adversary_messages.html', title='Messages', msg_form=msg_form, adv_msg_edit_form=adv_msg_edit_form,
			adv_next_round_form=adv_next_round_form, message=display_message, can_decrypt = can_decrypt_curr_message, game=current_game, msg_list_size=current_game.adv_current_msg_list_size, prev_msgs=prev_msgs_tuple, prev_msg_flag=0,usernames=usernames, msgs=msgs_tuple)
		
		else:
			# display normally
			return render_template('adversary_messages.html', title='Messages', msg_form=msg_form, adv_msg_edit_form=adv_msg_edit_form,
			adv_next_round_form=adv_next_round_form, message=display_message, can_decrypt = can_decrypt_curr_message, game=current_game, msg_list_size=current_game.adv_current_msg_list_size, prev_msgs=prev_msgs_tuple, prev_msg_flag=0, usernames=usernames, msgs=msgs_tuple)
		
# game setup route for the game master
@app.route('/game_setup', methods=['GET', 'POST']) #POST is enabled here so that users can give the website information to create messages with
@login_required #requires the user to be logged in
def game_setup():
	if current_user.role != 2: #if the user isn't a game master
		flash(f'Your permissions are insufficient to access this page.', 'danger') #flash error message
		return render_template('home.html', title='Home') #display the home page when they try to access this page directly.

	#seutp the forms the gm uses
	mng_form = GMManageGameForm()
	setup_form = GMSetupGameForm()
	usr_form = GMManageUserForm()

	#grab the state of the submit buttons so they only need to be pressed once
	is_mng_submit = mng_form.end_game.data
	is_setup_submit = setup_form.create_game.data
	is_usr_form = usr_form.update.data

	#create list of usernames for checkboxes
	users = User.query.filter_by(role=4).all()
	usernames = []
	for user in users:
		usernames.append(user.username)

	#game setup
	if is_setup_submit and setup_form.validate(): #when the create game button is pressed and the form is valid
		#capture the list of players from the checkboxes and make it into a string delimited by commas
		checkbox_output_list = request.form.getlist('players')
		checkbox_output_str = ''.join(map(str, checkbox_output_list))
		players = checkbox_output_str[:len(checkbox_output_str)-2] #len-2 is so that the last comma and space is removed from the last username


		#validation" since I don't know how to use the flaskform validation with a custom form, we call the validation in the setup form
		#doing it this way is kinda janky, the error messages don't look the same as other validation, but it works
		try:
			GMSetupGameForm.validate_players_checkbox(players)
		except ValidationError:
			#if validation for players fails, display an error and refresh the page so the game doesn't get created
			flash(f'One of the selected users is already in a game.', 'danger')
			return render_template('game_setup.html', title='Game Setup', mng_form=mng_form, setup_form=setup_form, usr_form=usr_form, usernames=usernames)

		#create the game with info from the form
		new_game = Game(name=setup_form.name.data, is_running=True, adversary=setup_form.adversary.data.username, players=players, current_round=1, adv_current_msg=0, adv_current_msg_list_size=0)
		db.session.add(new_game) #send to db
		db.session.commit()
		game = Game.query.order_by(-Game.id).filter_by(adversary=setup_form.adversary.data.username,players=players).first() #this finds the last game in the db with the passed players and adversary
		adv = User.query.filter_by(username=setup_form.adversary.data.username).first() #grab the adversary user of the game we just made
		adv.game = game.id #set their game to this game
		db.session.commit()
		player_list = []
		player_list = str_to_list(players, player_list)
		for player in strip_list_str(player_list): #for each player in the string of players
			user = User.query.filter_by(username=player).first() #grab their user object
			user.game = game.id #set their game to this game
			db.session.commit()
		flash(f'The game ' + setup_form.name.data + ' has been created.', 'success') #flash success message
		socketio.emit('ingame',broadcast=True)
		
	#game management
	if is_mng_submit and mng_form.validate(): #when the end game button is pressed and the form is valid
		game = Game.query.filter_by(name=mng_form.game.data.name).first()
		game.is_running = False
		adv = User.query.filter_by(username=game.adversary).first() #find the game's adversary
		adv.game = None #remove the game from the user
		db.session.commit() #commit
		player_list = []
		player_list = str_to_list(game.players, player_list) #grab a list of players from the game
		for player in player_list:
			user = User.query.filter_by(username=player).first() #find each of the player objects
			user.game = None #remove the game from the user
			db.session.commit() #commit
		flash(f'The game has been ended.', 'success') #show success message upon completion

		#pull the forms again because their information has updated, might not need to do this
		mng_form = GMManageGameForm()
		setup_form = GMSetupGameForm()

	#user management
	if is_usr_form and usr_form.validate(): #when the edit user button is pressed and the form is valid
		user = User.query.filter_by(username=usr_form.user.data.username).first() #grab the targeted user
		if user.game: #if the user is in a game
			#show an error message. changing a user's role while they are in a game will break stuff
			flash(f'Unable to change a user\'s role while they are in a game. Please end the game first.', 'danger')
			return render_template('game_setup.html', title='Game Setup', mng_form=mng_form, setup_form=setup_form, usr_form=usr_form)
		if usr_form.role.data == 'adv': #if the selected new role is adversary
			if user.role == 3:
				# show an error message. can't change a user's role to what they already are
				flash(f"You cannot change a user's role to what it already is!", 'danger')
				return render_template('game_setup.html', title='Game Setup', mng_form=mng_form, setup_form=setup_form, usr_form=usr_form)
			user.role = 3 #update to adversary
		if usr_form.role.data == 'usr': #if the selected new role is user
			if user.role == 4:
				# show an error message. can't change a user's role to what they already are
				flash(f"You cannot change a user's role to what it already is!", 'danger')
				return render_template('game_setup.html', title='Game Setup', mng_form=mng_form, setup_form=setup_form, usr_form=usr_form)
			user.role = 4 #update to user
		if usr_form.role.data == 'spec': #if the selected new role is spectator
			if user.role == 5:
				# show an error message. can't change a user's role to what they already are
				flash(f"You cannot change a user's role to what it already is!", 'danger')
				return render_template('game_setup.html', title='Game Setup', mng_form=mng_form, setup_form=setup_form, usr_form=usr_form)
			user.role = 5 #update to spectator
		db.session.commit()
		flash(f'The user ' + usr_form.user.data.username + ' has been updated.', 'success') #flash success message

	#display webpage normally
	return render_template('game_setup.html', title='Game Setup', mng_form=mng_form, setup_form=setup_form, usr_form=usr_form, usernames=usernames)

# Route for spectating
@app.route('/spectate', methods=['GET', 'POST']) #POST is enabled here so that users can give the website information
@login_required  # user must be logged in
def spectate_game():

	game_id = request.args.get('game_id')
	if game_id != None :
		game = Game.query.filter_by(id=game_id).first()
		messages = Message.query.filter_by(game=game_id).all()
		msg_count = len(Message.query.filter_by(game=game.id).all())
		
		return render_template('spectator_messages.html', title='Spectating', game=game, message=messages, msg_count=msg_count)

	# If the user is not a spectator, flash a warning and send back to home
	if current_user.role != 5 and current_user.role != 2:
		flash(f'Your permissions are insufficient to access this page.', 'danger')
		return render_template('home.html', title='Home')
	else:
		# Form for the selected game from running games list
		select_game_form = GameSelectForm()
		game_selected = select_game_form.select_game.data
		# If the game is selected and the form is validated, move to spectator_game page
		if game_selected and select_game_form.validate():
			game = select_game_form.running_games.data
			msg_count = len(Message.query.filter_by(game=game.id).all())
			messages = Message.query.filter_by(game=game.id).all()
			return render_template('spectator_messages.html', title='Spectating '+game.name, game=game, message=messages, sg_form=select_game_form, msg_count=msg_count)
		else:
			# Send list of games to template
			return render_template('spectator_messages.html', title='Spectate A Game', sg_form=select_game_form)

@app.route('/character_select', methods=['GET', 'POST']) #POST is enabled here so that users can give the website information
#@login_required  # user must be logged in
def character_select():
	#player_list = str_to_list(players, player_list)
	#for player in strip_list_str(player_list): #for each player in the string of players
	
	db.drop_all()
	db.session.commit()
	db.create_all()

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
	
	return render_template('character_select.html', title='Select Your Character')
		
@app.route('/end_of_game', methods=['GET', 'POST']) #POST is enabled here so that users can give the website information
#@login_required  # user must be logged in
def end_of_game():
	game = None;
	
	if (current_user.role == 3):
		game = Game.query.filter_by(adversary=current_user.username, is_running=True).first()
		if(game.end_result == game.adv_vote):
			return render_template('end_of_game.html', title='Results', game=game, result="Winner")
	else:
		games = Game.query.filter_by(is_running=True).all() #grab all the running games
		for g in games:
			game = g
			if check_for_str(game.players, current_user.username): #check if the current_user is in the target game
				if(game.end_result != game.adv_vote):
					return render_template('end_of_game.html', title='Results', game=game, result="Winner")
			
	return render_template('end_of_game.html', title='Results', game=game, result="Loser")

#sample route for testing pages
#when you copy this to test a page, make sure to change all instances of "testing"
#@app.route('/testing') #this decorator tells the website what to put after the http://<IP>
#@app.route('/testing', methods=['GET', 'POST']) #this is needed if the user is doing to submit forms and things
#@login_required #enforce that the user is logged in
#def testing():
#	return render_template('testing.html', title='Testing') #this tells the app what html template to use. #Title isn't needed

def update():
	#print("update")
	socketio.emit('update',broadcast=True)

@socketio.on('cast_vote')
def cast_vote(json):
	print(json)
	
	game = Game.query.filter_by(id=json['game_id']).first()
	
	if (current_user.role == 3):
		game.adv_vote = json['vote']
		db.session.commit()
	
	votes_list = []
	try: 
		votes_list = str_to_list(game.votes, votes_list) 
	except:
		pass
			
	who_voted = []
	try: 
		who_voted = str_to_list(game.who_voted, who_voted) 
	except:
		pass
	
	if (current_user.username not in who_voted) and current_user.role != 3:
		who_voted.append(current_user.username)
		game.who_voted = ', '.join(who_voted)
		db.session.commit()
		
		votes_list.append(json['vote'])
		game.votes = ', '.join(votes_list)
		db.session.commit()
		
	player_list = []
	str_to_list(game.players, player_list) 
		
	if (len(votes_list) >= len(player_list) and game.adv_vote != None):
		c = Counter(votes_list)
		game.end_result = c.most_common()[0][0];
		if(c.most_common()[0][1] == 1):
			game.end_result = game.adv_vote;  
		db.session.commit()
		socketio.emit('end_game',broadcast=True)
	
	print(current_user, " ", game);
		
	
@socketio.on('ready_to_vote')
def ready_to_vote(json):
	#print(json)

	game = Game.query.filter_by(id=json['game_id']).first()
	
	# try for the cases where no player has voted yet
	voted_list = []
	try: 
		voted_list = str_to_list(game.vote_ready, voted_list) 
	except:
		pass
	
	if json['player'] not in voted_list:
		voted_list.append(json['player'])
		game.vote_ready = ', '.join(voted_list)
		db.session.commit()
	
	player_list = []
	player_list = str_to_list(game.players, player_list)
	
	if (len(voted_list) / len(player_list) >= .5):
		print("lets vote")
		socketio.emit('start_vote',broadcast=True)
		
	print(current_user, " ", game);
	
	
	