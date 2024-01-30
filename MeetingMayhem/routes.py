"""
File: routes.py
Author: Robert Shovan /Voitheia
Date Created: 6/15/2021
Last Modified: 7/14/2021
E-mail: rshovan1@umbc.edu
Description: python file that handles the routes for the website.
"""
import random

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
from flask import render_template, session
from .models import User
from flask import render_template, url_for, flash, redirect, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from wtforms.validators import ValidationError
from MeetingMayhem import app, db, bcrypt, socketio
from MeetingMayhem.forms import GMManageUserForm, RegistrationForm, LoginForm, MessageForm, AdversaryMessageEditForm, AdversaryAdvanceRoundForm, GMManageGameForm, GMSetupGameForm, GameSelectForm
from MeetingMayhem.models import User, Message, Game
from MeetingMayhem.helper import check_for_str, strip_list_str, str_to_list, create_message, decrypt_button_show,decrypt_button_show_for_adv
from datetime import datetime
from collections import Counter
from flask import Flask, send_from_directory
import pytz

#root route, basically the homepage, this page doesn't really do anything right now
#having two routes means that flask will put the same html on both of those pages
#by using the render_template, we are able to pass an html document to flask for it to put on the web server

@app.route('/home') #likewise, this line is for http:/<IP>:5000/home
def home():
    if current_user.is_anonymous: #ask the user to login or register if they aren't logged in
        flash(f'Please register for an account or login to proceed.', 'info')
    elif not current_user.game and (current_user.role == 3 or current_user.role == 4): #if the user is logged in but isn't in a game, display below message
        flash(f'You are not currently in a game. Please have your game master create a game to proceed.', 'info')
    return render_template('home.html', title='Home') #this line passes the template we want to use and any variables it needs to it

@app.route('/') #this line states that if the user tries to access http:/<IP>:5000/ it will use the home funcito
@app.route('/homepage')
def homepage():
    if current_user.is_anonymous: #ask the user to login or register if they aren't logged in
        flash(f'Please register for an account or login to proceed.', 'info')
    elif not current_user.game and (current_user.role == 3 or current_user.role == 4): #if the user is logged in but isn't in a game, display below message
        flash(f'You are not currently in a game. Please have your game master create a game to proceed.', 'info')
    return render_template('homepage.html', title='HomePage') #this line passes the template we want to use and any variables it needs to it

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
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, role='4',image_url=form.selected_image.data) #create the user for the db
        db.session.add(user) #stage the user for the db
        db.session.commit() #commit new user to db
        flash(f'Your account has been created! Please login.', 'success') #flash a success message to let the user know the account was made

        socketio.emit('new_player')

        return redirect(url_for('login')) #redir the user to the login page
    return render_template('register.html', title='Register', form=form)

#login page route
@app.route('/login', methods=['GET', 'POST']) #POST is enabled here so that users can give the website information to login with
def login():
    if current_user.is_authenticated:
        return redirect(url_for('homepage')) #if the user is logged in, redir to home
    #     elif current_user.role==2:
    #         return redirect(url_for('game_setup'))
    form = LoginForm() #specify which form to use
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first() #check that the user exists, using username because that's what the user uses to log in
        if user and bcrypt.check_password_hash(user.password, form.password.data): #if the user exists and the password is correct
            if(user.role == 6): #If user's role is "inactive"
                next_page = request.args.get('next')  # check if the next argument exists (i.e. user tried to go somewhere they needed to login to see)
                flash(f'You cannot login because you have been removed from the game.','danger')  # Do not allow user to login
            else:
                login_user(user, remember=form.remember.data) #log the user in, and if the user checked the remeber box, remember the user (not sure if remember actually works)
                next_page = request.args.get('next') #check if the next argument exists (i.e. user tried to go somewhere they needed to login to see)
                flash(f'You are now logged in!', 'success') #notify the user they are logged in
            return redirect(next_page) if next_page else redirect(url_for('homepage')) #redir the user to the next_page arg if it exists, if not send them to home page
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
    current_game = Game.query.filter_by(is_running=True).first()
    # print(current_game.votes)
    # print(current_game.who_voted)
    # print("!!!!")
    if form.advance_round.data and current_game:
        current_game.current_round -= 1
        current_game.adv_current_msg = 0
        current_game.adv_current_msg_list_size = 0
        db.session.commit()
    return render_template('account.html', title='Account',result=current_game.vote_ready)

#message page
#TODO: check for duplicate post request when sending messages
@app.route('/messages', methods=['GET', 'POST']) #POST is enabled here so that users can give the website information to create messages with
@login_required
def messages():
    # -----------------------------------------------------------------------------------------------------------
    #If current user is a gmaster, send them to the homepage
    if current_user.role == 2:
        return render_template('home.html', title='Home')
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
    adversaries = User.query.filter_by(role=3, game=current_game.id).all()
    usernames = []
    other_name = [] # Name except current user
    image_url = []
    for user in users:
        usernames.append((user.username,user.image_url))
    for adversary in adversaries:
        usernames.append((adversary.username,adversary.image_url))
    #usernames = random.sample(usernames, len(usernames)) # randomizes usernames
    usernames = sorted(usernames)
    for username,url_image in usernames:
        if current_user.username != username:
            other_name.append(username)
            image_url.append(url_image)
    forms = {key: MessageForm() for key, _ in zip(other_name,range(len(other_name)))}#use the standard message form

    #sent and recieved messages
    sent_msg = [Message.query.filter_by(initial_sender=current_user.username, initial_recipient = name, game=current_game.id,adv_processed=False).all() for name in other_name]
    #print(sent_msg)
    recieved_msg = [Message.query.filter_by(edited_recipient=current_user.username,edited_sender=name,adv_processed=True, is_deleted=False, game=current_game.id).all() for name in other_name]
   
    # Organize messages by chatbox
    msgs_tuple = []
    
    for index in range(len(other_name)):
        msg_tuple_list = []
        if recieved_msg[index]:
            for message in recieved_msg[index]:
                if message.time_recieved == "Null":
                    message.time_recieved  = datetime.now(pytz.timezone("US/Central")).strftime("%b.%d.%Y-%H.%M")
                # False means to this message is on the right (recieved)
                msg_tuple_list.append((message, decrypt_button_show(message),message.time_recieved,True))
                db.session.commit()
        if sent_msg[index]:
            for message in sent_msg[index]:
                msg_tuple_list.append((message, None,message.time_sent,False))
                db.session.commit()
        msgs_tuple.append(msg_tuple_list)


    #setup message flag to tell template if it should display messages or not
    msg_flag = [True if msg_list else False for msg_list in msgs_tuple]
    msgs_tuple = [sorted(msgs_tuple_list, key=lambda x: datetime.strptime(x[2], "%b.%d.%Y-%H.%M"),reverse=False) if msgs_tuple else msgs_tuple for msgs_tuple_list in msgs_tuple]
    
    for name, form in forms.items():
        if form.validate_on_submit(): #when the user submits the message form and it is valid
            sent_str = request.form.get("submit")[16:]
            if sent_str.strip() != name.strip():
                continue
            if form.data["meet_time"] == "Time" or form.data["meet_location"] == "Locations":
                flash(f'Please select a time and location.', 'danger')
                return render_template('messages.html', title='Messages', forms=forms, game=current_game, 
                                msgs_tuple=msgs_tuple,msgs_flag=msg_flag, 
                                usernames=usernames,other_names=other_name,image_url=image_url)

            #ensure keys entered are keys of actual recipients chosen
            curr_time = datetime.now(pytz.timezone("US/Central")).strftime("%b.%d.%Y-%H.%M")
            _,msg_new = create_message(current_user, current_game, request.form, form, name, curr_time)
            msgs_tuple[other_name.index(name)].append((msg_new, None,msg_new.time_sent,False))
            update()
    
    #print(msg_flag)
    return render_template('messages.html', title='Messages', forms=forms, game=current_game, 
                            msgs_tuple=msgs_tuple,msgs_flag=msg_flag, 
                            usernames=usernames,other_names=other_name,image_url=image_url)



@app.route('/multilevelmessages', methods=['GET', 'POST']) #POST is enabled here so that users can give the website information to create messages with
@login_required
def multiLevelMessages():
    pass

def adv_messages_page():
    #setup the current_game so that we can pull information from it
    current_game = Game.query.filter_by(adversary=current_user.username, is_running=True).first()
    #create list of usernames for checkboxes
    users = User.query.filter_by(role=4, game=current_game.id).all()
    usernames = []
    other_name = [] # Agents name
    image_url = []
    adversaries = User.query.filter_by(role=3, game=current_game.id).all()
    for user in users:
        usernames.append((user.username,user.image_url))
    for adversary in adversaries:
        usernames.append((adversary.username,adversary.image_url))
    usernames = sorted(usernames)
    for username,url_image in usernames:
        if current_user.username != username:
            other_name.append(username)
            image_url.append(url_image)
    pretend_name = [other_name[-1], other_name[0]]
    #messages not being processed yet
    forms = {key: MessageForm() for key, _ in zip(other_name,range(len(other_name)))}#use the standard message form
    forms[other_name[0]+ "_" + other_name[1]] = AdversaryMessageEditForm()
    adv_msg_edit_form = forms[other_name[0]+ "_" + other_name[1]]
    #sent and recieved messages
    sent_msg = [Message.query.filter_by(sender=current_user.username, recipient = name, game=current_game.id,adv_submitted=False).all() for name in other_name]
    #print(sent_msg)
    recieved_msg = [Message.query.filter_by(new_recipient=current_user.username,sender=name,adv_submitted=True, is_deleted=False, game=current_game.id).all() for name in other_name]
   
    # Organize messages by chatbox
    msgs_tuple = []
    
    for index in range(len(other_name)):
        msg_tuple_list = []
        if recieved_msg[index]:
            for message in recieved_msg[index]:
                if message.time_recieved == "Null":
                    message.time_recieved  = datetime.now(pytz.timezone("US/Central")).strftime("%b.%d.%Y-%H.%M")
                # False means to this message is on the right (recieved)
                msg_tuple_list.append((message, decrypt_button_show(message),message.time_recieved,True))
                db.session.commit()
        if sent_msg[index]:
            for message in sent_msg[index]:
                msg_tuple_list.append((message, None,message.time_sent,False))
                db.session.commit()
        msgs_tuple.append(msg_tuple_list)


    #setup message flag to tell template if it should display messages or not
    msg_flag = [True if msg_list else False for msg_list in msgs_tuple]
    msgs_tuple = [sorted(msgs_tuple_list, key=lambda x: datetime.strptime(x[2], "%b.%d.%Y-%H.%M"),reverse=False) if msgs_tuple else msgs_tuple for msgs_tuple_list in msgs_tuple]
    display_message = None
    is_submit_edits = adv_msg_edit_form.submit_edits.data
    is_delete_msg = adv_msg_edit_form.delete_msg.data
    
    messageToBeProcessed12 = Message.query.filter_by(sender=other_name[0], recipient = other_name[1], game=current_game.id).all()
    messageToBeProcessed21 = Message.query.filter_by(sender=other_name[1], recipient = other_name[0], game=current_game.id).all()
    editMessage = []
    for msg in messageToBeProcessed12:
        editMessage.append((msg, decrypt_button_show_for_adv(msg,current_user.username,msg.encryption_details, msg.is_encrypted or msg.is_signed),None,True))
    for msg in messageToBeProcessed21:
        editMessage.append((msg, decrypt_button_show_for_adv(msg,current_user.username,msg.encryption_details, msg.is_encrypted or msg.is_signed),None,False))
    # print("!!!!!!!!!!!!!")
    # print(editMessage)
    #! If adversary submit the form 
    for name, form in forms.items():
        if form.validate_on_submit(): #when the user submits the message form and it is valid
            sent_str = request.form.get("submit")[16:]
            if sent_str.strip() != name.strip():
                continue
            if form.data["meet_time"] == "Time" or form.data["meet_location"] == "Locations":
                flash(f'Please select a time and location.', 'danger')
                return render_template('messages.html', title='Messages', forms=forms, game=current_game, 
                                 msgs_tuple=msgs_tuple,msgs_flag=msg_flag, message = display_message,editMessage=editMessage,
                                usernames=usernames,other_names=other_name,image_url=image_url, pretend_name=pretend_name)

            #ensure keys entered are keys of actual recipients chosen
            curr_time = datetime.now(pytz.timezone("US/Central")).strftime("%b.%d.%Y-%H.%M")
            _,msg_new = create_message(current_user, current_game, request.form, form, name, curr_time)
            update()
            msgs_tuple[other_name.index(name)].append((msg_new, None,msg_new.time_sent,False))
            return render_template('adversary_messages.html', title='Messages', forms=forms, game=current_game, 
                            msgs_tuple=msgs_tuple,msgs_flag=msg_flag, message = display_message,editMessage=editMessage,
                            usernames=usernames,other_names=other_name,image_url=image_url, pretend_name=pretend_name)
    #adversary message editing
    
    if is_submit_edits : #if any of the prev/next/submit buttons are clicked
        display_message = Message.query.filter_by(id=adv_msg_edit_form.msg_num.data).first()
        new_recipients = request.form.getlist('newrecipients')
        new_senders= request.form.getlist('newsenders')
        new_recipients = new_recipients[0]
        new_senders = new_senders[0]
        #! Validation
        if not new_recipients :
            flash(f'Please select one recipient.', 'danger')
            return render_template('adversary_messages.html', title='Messages', forms=forms, game=current_game, 
                        msgs_tuple=msgs_tuple,msgs_flag=msg_flag, message = display_message,editMessage=editMessage,
                        usernames=usernames,other_names=other_name,image_url=image_url, pretend_name=pretend_name)
        if not new_senders:
            flash(f'Please select one sender.', 'danger')
            return render_template('adversary_messages.html', title='Messages', forms=forms, game=current_game, 
                        msgs_tuple=msgs_tuple,msgs_flag=msg_flag, message = display_message,editMessage=editMessage,
                        usernames=usernames,other_names=other_name,image_url=image_url, pretend_name=pretend_name)
        if new_senders == new_recipients:
                flash(f'Please do not select same sender and recipient.', 'danger')
                return render_template('adversary_messages.html', title='Messages', forms=forms, game=current_game, 
                            msgs_tuple=msgs_tuple,msgs_flag=msg_flag, message = display_message,editMessage=editMessage,
                            usernames=usernames,other_names=other_name,image_url=image_url, pretend_name=pretend_name)
            
        #setup the changes to be made to the current message
        encryption_type = request.form.get("encryption_type_select2")
        encrypted_key = request.form.get("encryption_key2")
        display_message.new_sender = new_senders
        display_message.new_recipient = new_recipients
        display_message.edited_content = adv_msg_edit_form.edited_content.data if not adv_msg_edit_form.not_editable.data else display_message.content
        encrypted_keys = []
        signed_keys = []
        if  encryption_type == 'symmetric':
            display_message.encryption_type = encryption_type
            display_message.key = encrypted_key
            if (new_senders in encrypted_key) and (new_recipients in encrypted_key):
                encrypted_keys.append(encrypted_key)
            else:
                encrypted_keys.append('Warning: Recipient cannot decrypt the message with this key.')
        elif encryption_type  == 'asymmetric':
            display_message.encryption_type = encryption_type
            display_message.key = encrypted_key
            if encrypted_key == 'public_' + new_recipients:
                encrypted_keys.append(encrypted_key)
            elif encrypted_key == 'private_' + str(new_senders):
                encrypted_keys.append('Warning: Wrong way to execute asymmetric encryption.')
            else:
                encrypted_keys.append('Warning: Recipient cannot decrypt the message with this key.')
        elif encryption_type  == 'signed':
            display_message.encryption_type = encryption_type
            display_message.key = encrypted_key
            if encrypted_key == 'private_' + str(new_senders):
                signed_keys.append(encrypted_key)
            elif encrypted_key == 'public_' + new_recipients:
                signed_keys.append("Warning: but a signature usually requires the sender's private key.")
            else:
                signed_keys.append('Warning: Recipient cannot decrypt the message with this key.')
        else:
                    # no-add on: not edited
            display_message.is_edited = False

            if display_message.edited_content != display_message.content or display_message.sender != display_message.new_sender or   display_message.recipient != display_message.new_recipient:
                display_message.is_edited = True

                display_message.is_signed = len(signed_keys) > 0
                display_message.is_encrypted = len(encrypted_keys) > 0
                display_message.encryption_details = ", ".join(map(str, encrypted_keys))
                display_message.signed_details = ", ".join(map(str, signed_keys))

            elif display_message.sender != display_message.new_sender or   display_message.recipient != display_message.new_recipient:
                display_message.is_edited = True
                encrypted_keys = []
                signed_keys = []
                encrypted_key = display_message.key
                encryption_type = display_message.encryption_type
                if  encryption_type == 'symmetric':
                    if (new_recipients in encrypted_key):
                        encrypted_keys.append(encrypted_key)
                    else:
                        encrypted_keys.append('Warning: Recipient cannot decrypt the message with this key.')
                elif encryption_type  == 'asymmetric':
                    if encrypted_key == 'public_' + new_recipients:
                        encrypted_keys.append(encrypted_key)
                    elif "private" in encrypted_key:
                    #elif encrypted_key == 'private_' + str(new_senders):
                        encrypted_keys.append('Warning: Wrong way to execute asymmetric encryption.')
                    else:
                        encrypted_keys.append('Warning: Recipient cannot decrypt the message with this key.')
                elif encryption_type  == 'signed':
                    if "private" in encrypted_key:
                    #if encrypted_key == 'private_' + str(new_senders):
                        signed_keys.append(encrypted_key)
                    elif encrypted_key == 'public_' + new_recipients:
                        signed_keys.append("Warning: but a signature usually requires the sender's private key.")
                    else:
                        signed_keys.append('Warning: Recipient cannot decrypt the message with this key.')
                display_message.is_signed = len(signed_keys) > 0
                display_message.is_encrypted = len(encrypted_keys) > 0
                display_message.encryption_details = ", ".join(map(str, encrypted_keys))
                display_message.signed_details = ", ".join(map(str, signed_keys))
            
            display_message.adv_submitted = True
            db.session.commit()
    elif is_delete_msg: #if the delete message button is clicked
        #flag the message as edited and deleted
        display_message = Message.query.filter_by(id=adv_msg_edit_form.msg_num.data).first()
        display_message.adv_submitted = True
        display_message.is_edited = True
        display_message.is_deleted = True
        db.session.commit()

    is_submit_edits = False
    is_delete_msg = False
    update()
    return render_template('adversary_messages.html', title='Messages', forms=forms, game=current_game, 
                            msgs_tuple=msgs_tuple,msgs_flag=msg_flag, message = display_message,editMessage=editMessage,
                            usernames=usernames,other_names=other_name,image_url=image_url, pretend_name=pretend_name)

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
    is_end_game_page_submit = mng_form.end_game_page.data
    is_setup_submit = setup_form.create_game.data
    is_usr_form = usr_form.update.data
    is_usr_profile = usr_form.update_profile.data
    is_random_adv = mng_form.random.data

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
        socketio.emit('ingame')

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

    #bring the selected game to the end game screen, used for testing
    if is_end_game_page_submit and mng_form.validate():
        game = Game.query.filter_by(name=mng_form.game.data.name).first()
        game.end_result = "testing"
        db.session.commit()
        socketio.emit('end_game')
        flash(f'The game has been brought to the end game page.', 'success')

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
        if usr_form.role.data == 'inac': #if the selected new role is inactive
            if user.role == 6:
                # show an error message. can't change a user's role to what they already are
                flash(f"You cannot change a user's role to what it already is!", 'danger')
                return render_template('game_setup.html', title='Game Setup', mng_form=mng_form, setup_form=setup_form, usr_form=usr_form)
            user.role = 6 #update to spectator
        db.session.commit()
        flash(f'The user ' + usr_form.user.data.username + ' has been updated.', 'success') #flash success message
        update()
    # Manage Profile
    if is_usr_profile and usr_form.validate():
        user = User.query.filter_by(username=usr_form.user.data.username).first()
        user.image_url = usr_form.profile.data
        db.session.commit()
        flash(f'The user ' + usr_form.user.data.username + ' profile has been updated.', 'success') #flash success message
        update()
    if is_random_adv and mng_form.validate():
        game = Game.query.filter_by(name=mng_form.game.data.name).first()
        adv = User.query.filter_by(username=game.adversary).first()
        adv.role = 4
        player_list = []
        player_list = str_to_list(game.players, player_list) #grab a list of players from the game
        player_list.append(game.adversary)
        import random
        random_adv = random.randint(0, 2)
        selected_adv = User.query.filter_by(username=player_list[random_adv]).first()
        selected_adv.role = 3
        game.adversary = selected_adv.username
        del player_list[random_adv]
        game.players = ", ".join(player_list)
        db.session.commit()
        # print(selected_adv)
        # print(User.query.filter_by(username=player_list[0]).first())
        # print(User.query.filter_by(username=player_list[1]).first())
        # print(game.players)
        # flash(f'The user ' + selected_adv.username + ' has been selected as adv', 'success')
        update()


    #display webpage normally
    return render_template('game_setup.html', title='Game Setup', mng_form=mng_form, setup_form=setup_form, usr_form=usr_form, usernames=usernames)

@app.route('/game_setup_multi', methods=['GET', 'POST']) #POST is enabled here so that users can give the website information to create messages with
@login_required #requires the user to be logged in
def game_setup_multi():
    if current_user.role != 2: #if the user isn't a game master
        flash(f'Your permissions are insufficient to access this page.', 'danger') #flash error message
        return render_template('home.html', title='Home') #display the home page when they try to access this page directly.

    #seutp the forms the gm uses
    mng_form = GMManageGameForm()
    setup_form = GMSetupGameForm()
    usr_form = GMManageUserForm()

    #grab the state of the submit buttons so they only need to be pressed once
    is_mng_submit = mng_form.end_game.data
    is_end_game_page_submit = mng_form.end_game_page.data
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
        socketio.emit('ingame')

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

    #bring the selected game to the end game screen, used for testing
    if is_end_game_page_submit and mng_form.validate():
        game = Game.query.filter_by(name=mng_form.game.data.name).first()
        game.end_result = "testing"
        db.session.commit()
        socketio.emit('end_game')
        flash(f'The game has been brought to the end game page.', 'success')

    #user management
    if is_usr_form and usr_form.validate(): #when the edit user button is pressed and the form is valid
        user = User.query.filter_by(username=usr_form.user.data.username).first() #grab the targeted user
        if user.game: #if the user is in a game
            #show an error message. changing a user's role while they are in a game will break stuff
            flash(f'Unable to change a user\'s role while they are in a game. Please end the game first.', 'danger')
            return render_template('game_setup_multi.html', title='Game Setup', mng_form=mng_form, setup_form=setup_form, usr_form=usr_form)
        if usr_form.role.data == 'adv': #if the selected new role is adversary
            if user.role == 3:
                # show an error message. can't change a user's role to what they already are
                flash(f"You cannot change a user's role to what it already is!", 'danger')
                return render_template('game_setup_multi.html', title='Game Setup', mng_form=mng_form, setup_form=setup_form, usr_form=usr_form)
            user.role = 3 #update to adversary
        if usr_form.role.data == 'usr': #if the selected new role is user
            if user.role == 4:
                # show an error message. can't change a user's role to what they already are
                flash(f"You cannot change a user's role to what it already is!", 'danger')
                return render_template('game_setup_multi.html', title='Game Setup', mng_form=mng_form, setup_form=setup_form, usr_form=usr_form)
            user.role = 4 #update to user
        if usr_form.role.data == 'spec': #if the selected new role is spectator
            if user.role == 5:
                # show an error message. can't change a user's role to what they already are
                flash(f"You cannot change a user's role to what it already is!", 'danger')
                return render_template('game_setup_multi.html', title='Game Setup', mng_form=mng_form, setup_form=setup_form, usr_form=usr_form)
            user.role = 5 #update to spectator
        if usr_form.role.data == 'inac': #if the selected new role is inactive
            if user.role == 6:
                # show an error message. can't change a user's role to what they already are
                flash(f"You cannot change a user's role to what it already is!", 'danger')
                return render_template('game_setup_multi.html', title='Game Setup', mng_form=mng_form, setup_form=setup_form, usr_form=usr_form)
            user.role = 6 #update to spectator
        db.session.commit()
        flash(f'The user ' + usr_form.user.data.username + ' has been updated.', 'success') #flash success message
        update()

    #display webpage normally
    return render_template('game_setup_multi.html', title='Game Setup', mng_form=mng_form, setup_form=setup_form, usr_form=usr_form, usernames=usernames)

# Route for spectating
@app.route('/spectate', methods=['GET', 'POST']) #POST is enabled here so that users can give the website information
@login_required  # user must be logged in
def spectate_game():

    game_id = request.args.get('game_id')
    if game_id != None :
        game = Game.query.filter_by(id=game_id).first()
        messages = Message.query.filter_by(game=game_id).all()
        msg_count = len(Message.query.filter_by(game=game.id).all())
        for msg in messages:
            print(msg)
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
            for msg in messages:
                print(msg)
            return render_template('spectator_messages.html', title='Spectating '+game.name, game=game, message=messages, sg_form=select_game_form, msg_count=msg_count)
        else:
            # Send list of games to template
            return render_template('spectator_messages.html', title='Spectate A Game', sg_form=select_game_form)

"""
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
"""
'''
@app.route('/end_of_game', methods=['GET', 'POST']) #POST is enabled here so that users can give the website information
#@login_required  # user must be logged in
def end_of_game():
    game = None

    if (current_user.role == 3):
        game = Game.query.filter_by(adversary=current_user.username, is_running=True).first()
        if(game.end_result == "testing"):
            return render_template('end_of_game.html', title='Results', game=game, result="Testing")
        if(game.end_result == game.adv_vote):
            return render_template('end_of_game.html', title='Results', game=game, result="AdvWin")
        else:
            return render_template('end_of_game.html', title='Results', game=game, result="AdvLose")
    else:
    # change to say player winner vs what it curently does.
        games = Game.query.filter_by(is_running=True).all() #grab all the running games
        for g in games:
            game = g
            if check_for_str(game.players, current_user.username): #check if the current_user is in the target game
                if(game.end_result == "testing"):
                    return render_template('end_of_game.html', title='Results', game=game, result="Testing")
                if(game.end_result != game.adv_vote):
                    return render_template('end_of_game.html', title='Results', game=game, result="PlayerWin")
                else:
                    return render_template('end_of_game.html', title='Results', game=game, result="PlayerLose")

    return render_template('end_of_game.html', title='Results', game=game, result="Loser")
'''
#sample route for testing pages
#when you copy this to test a page, make sure to change all instances of "testing"
#@app.route('/testing') #this decorator tells the website what to put after the http://<IP>
#@app.route('/testing', methods=['GET', 'POST']) #this is needed if the user is doing to submit forms and things
#@login_required #enforce that the user is logged in
#def testing():
#	return render_template('testing.html', title='Testing') #this tells the app what html template to use. #Title isn't needed

def update():
    #print("update")
    socketio.emit('update')

@socketio.on('cast_vote')
@app.route('/messages', methods=['GET', 'POST'])
def cast_vote(json):
    current_game = Game.query.filter_by(id=json['game_id']).first()
    vote = json['vote']
    # current vote list
    votes_list = []
    votes_list = str_to_list(current_game.votes, votes_list)
    who_voted = []
    # current voted users
    who_voted = str_to_list(current_game.who_voted, who_voted)
    # user not vote before
    if current_user.username not in who_voted:
        who_voted.append(current_user.username)
        current_game.who_voted = ', '.join(who_voted)
        db.session.commit()

        votes_list.append(vote)
        current_game.votes = ', '.join(votes_list)
        db.session.commit()
    else:
        index = who_voted.index(current_user.username)
        votes_list[index] = vote
        current_game.votes = ', '.join(votes_list)
        db.session.commit()

    player_list = []
    str_to_list(current_game.players, player_list)
    current_game.vote_ready = ""
    print(votes_list)
    if len(votes_list) == len(player_list):
        c = Counter(votes_list)
        # The most common result
        current_game.end_result = c.most_common()[0][0]
        if len(c) == 1:
            current_game.vote_ready = "PlayerWin"
            db.session.commit()
            # print(current_game.votes)
            # print(current_game.vote_ready)
        else:
            current_game.vote_ready = "PlayerLose"
            db.session.commit()
            # print(current_game.votes)
            # print(current_game.vote_ready)
    socketio.emit("return_result",current_game.vote_ready)
    return

@socketio.on('adv_result')
def adv_result(json):
    socketio.emit("adv_show")
    current_game = Game.query.filter_by(id=json['game_id']).first()
    socketio.emit("return_result_for_adv",current_game.vote_ready)
    print(current_game.vote_ready)
    return

@socketio.on('ready_to_vote')
def ready_to_vote(json):
    game = Game.query.filter_by(id=json['game_id']).first()
    socketio.emit('start_vote')

@app.route('/images/<path:filename>')
def serve_images(filename):
    return send_from_directory('images', filename)

@socketio.on('decrypted')
def decrypted(json):
    display_message =  Message.query.filter_by(id=json["message"]).first()
    display_message.is_decrypted = True
    #display_message.is_edited = True
    db.session.commit()
    # print("*******************************************")
    # print(display_message)
    # print("*******************************************")

@socketio.on('Generate_Log')
def Generate_Log():
    import xlsxwriter
    current_game = Game.query.filter_by(is_running=True).first()
    messages = Message.query.filter_by(game=current_game.id).all()
    time_generated= datetime.now(pytz.timezone("US/Central")).strftime("%b.%d.%Y-%H.%M")
    workbook = xlsxwriter.Workbook('./Data/'+time_generated+".xlsx")
    worksheet = workbook.add_worksheet()

    header = ["Sender","Recipient","Content","Meet Time and Location","Time Sent","Time Recieved","Initial_is_encrypted","Initial_encryption_details","Initial_is_signed","Initial_signed_details","Adv_Created","Is Edited","Is Decrypted","New Sender","New Recipient","Edited Content","Is_encrypted","Encryption_details","Is_signed","Signed_details"]
    col = 0
    for item in header:
        worksheet.write(0, col, item)
        col += 1
    row = 1
    for msg in messages:
        worksheet.write(row, 0, msg.sender)
        worksheet.write(row, 1, msg.recipient)
        worksheet.write(row, 2, msg.content)
        worksheet.write(row, 3, msg.location_meet + " " + msg.time_meet + msg.time_am_pm)
        worksheet.write(row, 4, msg.time_sent)
        worksheet.write(row, 5, msg.time_recieved )
        worksheet.write(row, 6, str(msg.initial_is_encrypted))
        worksheet.write(row, 7, str(msg.initial_encryption_details))
        worksheet.write(row, 8, str(msg.initial_is_signed))
        worksheet.write(row, 9, str(msg.initial_signed_details))
        worksheet.write(row, 10, str(msg.adv_created))
        worksheet.write(row, 11, str(msg.is_edited))
        worksheet.write(row, 12, str(msg.is_decrypted))
        worksheet.write(row, 13, msg.new_sender)
        worksheet.write(row, 14, msg.new_recipient)
        worksheet.write(row, 15, msg.edited_content)
        worksheet.write(row, 16, str(msg.is_encrypted))
        worksheet.write(row, 17, str(msg.encryption_details))
        worksheet.write(row, 18, str(msg.is_signed))
        worksheet.write(row, 19, str(msg.signed_details))
        row +=1
    worksheet.write(row,0, "GAME INFO")
    row += 1
    worksheet.write(row, 0, str(current_game.id))
    worksheet.write(row, 1, str(current_game.name))
    worksheet.write(row, 2, str(current_game.adversary))
    worksheet.write(row, 3, str(current_game.players))
    worksheet.write(row, 4, str(current_game.vote_ready))
    worksheet.write(row, 5, str(current_game.votes))
    worksheet.write(row, 6, str(current_game.who_voted))
    worksheet.write(row, 7, str(current_game.end_result))
    workbook.close()
