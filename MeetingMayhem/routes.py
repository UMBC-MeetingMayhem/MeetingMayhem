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
from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, logout_user, login_required, current_user
from wtforms.validators import ValidationError
from MeetingMayhem import app, db, bcrypt
from MeetingMayhem.forms import GMManageUserForm, RegistrationForm, LoginForm, MessageForm, AdversaryMessageEditForm, AdversaryMessageButtonForm, AdversaryAdvanceRoundForm, AdversaryMessageSendForm, GMManageGameForm, GMSetupGameForm
from MeetingMayhem.models import User, Message, Game
from MeetingMayhem.helper import parse_for_username, parse_for_players, parse_for_game, check_for_str, strip_list_str

"""
all of this has been moved to helper.py, leaving it here for now until playtested properly
#TODO: need validation on all these helper methods to ensure that the string has contents

#recursivley parse the given string for usernames, return a list of usernames delimited by commas
def parse_for_username(str, users):
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

#recursivley parse the given string for players, return a list of players used for resetting a player's game when the game is ended
def parse_for_players(str, players):
    players.append(str.partition(', ')[0])
    str1=str.partition(', ')[2]
    if str1:
        parse_for_players(str1, players)
    return players

#same thing as the parse_for_username function, just for games instead
def parse_for_game(str, games):
    str1=str.partition("Name='")[2]
    str2=str1.partition("', ")
    if str2[2]:
        if (str2[2].find('Name') != -1):
            game = str2[0] + ', '
            games.append(game)
            parse_for_game(str2[2], games)
        else:
            games.append(str2[0])
    return games

#recursivley parse the given string for usernames, return true if the given username is found
def check_for_str(str, check):
    str1=str.partition(', ') #split the string into the username, the "', ", and the rest of the string
    if (str1[0] == check): #if the first part of str is the username we are looking for
        return True
    if (not str1[2]): #if there is nothing in the rest of str, it means there are no more usernames to look for
        return False
    else:
        return check_for_str(str1[2], check) #call this method again if there is more string to look through

#used to strip commas and white spaces out of lists of strings
def strip_list_str(str_list):
    new_str_list = []
    for str in str_list:
        new_str = str.partition(",")[0] #put everything before the comma into the new list
        new_str_list.append(new_str)
    return new_str_list
"""

#root route, basically the homepage, this page doesn't really do anything right now
#having two routes means that flask will put the same html on both of those pages
#by using the render_template, we are able to pass an html document to flask for it to put on the web server
@app.route('/') #this line states that if the user tries to access http:/<IP>:5000/ it will use the home funciton
@app.route('/home') #likewise, this line is for http:/<IP>:5000/home
def home():
    if current_user.is_anonymous: #ask the user to login or register if they aren't logged in
        flash(f'Please register for an account or login to proceed.', 'info')
    elif not current_user.game and current_user.role > 2: #if the user is logged in but isn't in a game, display below message
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

    if not current_user.game: #if the current user isn't in a game, send them to the homepage and display message
        flash(f'You are not currently in a game. Please have your game master put you in a game.', 'danger')
        return render_template('home.html', title='Home')

    #set the display_message to None initially so that if there is no message to display it doesn't break the website
    display_message = None

    #if the current_user is of adversary role, then display the adversary version of the page
    if (current_user.role==3):

        #setup the current_game so that we can pull information from it
        current_game = Game.query.filter_by(adversary=current_user.username, is_running=True).first()

        #setup variables for the forms the adversary needs to use
        msg_form = AdversaryMessageSendForm()
        adv_msg_edit_form = AdversaryMessageEditForm()
        adv_buttons_form = AdversaryMessageButtonForm()
        adv_next_round_form = AdversaryAdvanceRoundForm()

        #setup variable to contain the messages that are in the current_round of this game
        messages = Message.query.filter_by(round=current_game.current_round+1, game=current_game.id).all()
        
        if messages: #if messages has content, set the display message to the adversary's current message
            display_message = messages[current_game.adv_current_msg]

        else: #if there are no messages, set display message to none
            display_message = None

        #set the adv_current_msg_list_size so that the edit message box "scrolling" works correctly
        current_game.adv_current_msg_list_size = len(messages)
        
        #create variables for the edit message box buttons so that we only check their state once
        is_prev_submit = adv_buttons_form.prev_submit.data
        is_next_submit = adv_buttons_form.next_submit.data
        is_submit_edits = adv_msg_edit_form.submit_edits.data
        is_delete_msg = adv_buttons_form.delete_msg.data

        #grab the messages from previous rounds, this is done here because the previous messages shouldn't change
        prev_msgs = None
        if (current_game.current_round>2): #messages are created with current_round+1, so there shouldn't be a reason to display messages on rounds 1 or 2
            prev_messages = Message.query.filter_by(game=current_game.id).all() #grab all the previous messages for this game
            msg_round = current_game.current_round #create an "iterator" so messages are displayed in order of round
            prev_msgs = []
            while msg_round>=2: #there won't be any messages from round 1 because messages are created with current_round+1, so stop at round 2
                for message in prev_messages:
                    if message.round == msg_round: #if the target message matches the round we are parsing this loop
                        prev_msgs.append(message) #append it to the list
                msg_round -= 1 #decrement iterator

        #make a flag that the template uses to determine if it should display previous messages or not
        prev_msg_flag = True
        if not prev_msgs: #if the list of previous messages is empty, set the flag to false
            prev_msg_flag = False

        if msg_form.submit.data and msg_form.validate(): #if the adversary tries to send a message, and it is valid

            #if sender, recipient, or content are None, display an error
            if not msg_form.sender.data or not msg_form.recipient.data or not msg_form.content.data:
                flash(f'There was an error in creating your message. Please try again.', 'danger')
                return render_template('adversary_messages.html', title='Messages', msg_form=msg_form, adv_msg_edit_form=adv_msg_edit_form,
                adv_buttons_form=adv_buttons_form, adv_next_round_form=adv_next_round_form, message=display_message, game=current_game,
                current_msg=(current_game.adv_current_msg+1), msg_list_size=current_game.adv_current_msg_list_size, prev_msgs=prev_msgs, prev_msg_flag=prev_msg_flag)
            
            users_recipients=[] #make a list to put usernames in for the recipient
            users_senders=[] #make a list to put usernames in for the sender
            #this creates a string of user objects, maps the whole thing to a string, parses that string for only the usernames,
            #then maps the list of usernames into a string to pass into the db
            recipients = ''.join(map(str, parse_for_username(''.join(map(str, msg_form.recipient.data)), users_recipients)))
            senders = ''.join(map(str, parse_for_username(''.join(map(str, msg_form.sender.data)), users_senders)))

            #if the message is a duplicate display an error and don't put the message in the db
            if Message.query.filter_by(sender=senders, recipient=recipients, content=msg_form.content.data, round=current_game.current_round+1, game=current_game.id).first():
                flash(f'Duplicate message detected. Please try sending a different message.', 'danger')
                return render_template('adversary_messages.html', title='Messages', msg_form=msg_form, adv_msg_edit_form=adv_msg_edit_form,
                adv_buttons_form=adv_buttons_form, adv_next_round_form=adv_next_round_form, message=display_message, game=current_game,
                current_msg=(current_game.adv_current_msg+1), msg_list_size=current_game.adv_current_msg_list_size, prev_msgs=prev_msgs, prev_msg_flag=prev_msg_flag)

            #create the new message variable with the information from the form
            new_message = Message(round=(current_game.current_round+1), game=current_game.id, sender=senders, recipient=recipients, content=msg_form.content.data,
            is_edited=True, new_sender=None, new_recipient=None, edited_content=None, is_deleted=False)

            db.session.add(new_message) #stage the message
            db.session.commit() #commit the message to the db
            flash(f'Your message has been sent!', 'success') #success message to let user know it worked

            #render the webpage
            return render_template('adversary_messages.html', title='Messages', msg_form=msg_form, adv_msg_edit_form=adv_msg_edit_form,
            adv_buttons_form=adv_buttons_form, adv_next_round_form=adv_next_round_form, message=display_message, game=current_game,
            current_msg=(current_game.adv_current_msg+1), msg_list_size=current_game.adv_current_msg_list_size, prev_msgs=prev_msgs, prev_msg_flag=prev_msg_flag)
        
        elif (is_prev_submit or is_next_submit or is_submit_edits or is_delete_msg): #if any of the prev/next/submit buttons are clicked
            if is_prev_submit: #if the prev button is clicked
                if current_game.adv_current_msg == 0: #if the adversary tries to go backwards at the first message
                    current_game.adv_current_msg = (current_game.adv_current_msg_list_size - 1) #loop back around
                    db.session.commit() #update the current message

                else: #decrement the current message normally and update the value
                    current_game.adv_current_msg -= 1
                    db.session.commit()
            
            elif is_next_submit: #if the next button is clicked
                #if the adversary tries to go forwards on the last message
                if current_game.adv_current_msg == (current_game.adv_current_msg_list_size - 1):
                    current_game.adv_current_msg = 0 #loop back around
                    db.session.commit() #update the current message

                else: #increment the current message normally and update the value
                    current_game.adv_current_msg += 1
                    db.session.commit()
            
            #TODO: some sort of validation here? - not sure if needed cause users are chosen from dropdown/checkboxes
            elif is_submit_edits and adv_msg_edit_form.validate(): #if the submit button is clicked
            
                users_recipients=[] #make a list to put usernames in for the recipient
                users_senders=[] #make a list to put usernames in for the sender
                #this creates a string of user objects, maps the whole thing to a string, parses that string for only the usernames,
                #then maps the list of usernames into a string to pass into the db
                new_recipients = ''.join(map(str, parse_for_username(''.join(map(str, adv_msg_edit_form.new_recipient.data)), users_recipients)))
                new_senders = ''.join(map(str, parse_for_username(''.join(map(str, adv_msg_edit_form.new_sender.data)), users_senders)))
                #setup the changes to be made to the current message
                display_message.is_edited = True
                display_message.new_sender = new_senders
                display_message.new_recipient = new_recipients
                display_message.edited_content = adv_msg_edit_form.edited_content.data
                #pull the messages again since the messages we want to display has changed
                messages = Message.query.filter_by(round=current_game.current_round+1, game=current_game.id).all()
                current_game.adv_current_msg = 0
                current_game.adv_current_msg_list_size = len(messages)
                #commit the messages to the database
                db.session.commit()

            elif is_delete_msg: #if the delete message button is clicked
                #flag the message as edited and deleted
                display_message.is_edited = True
                display_message.is_deleted = True
                db.session.commit()
                #pull the messages again since the messages we want to display has changed
                messages = Message.query.filter_by(round=current_game.current_round+1, game=current_game.id).all()
                current_game.adv_current_msg = 0
                current_game.adv_current_msg_list_size = len(messages)
                #commit the messages to the database
                db.session.commit()

            #set the display_message to the message the adversary is currently looking at
            if (messages): #if messages has content, set the display message to the adversary's current message
                display_message = messages[current_game.adv_current_msg]

            else: #if there are no messages, set display message to none
                display_message = None

            #reset the variables that keep track of which button has been pressed
            is_prev_submit = False
            is_next_submit = False
            is_submit_edits = False
            is_delete_msg = False

            #render the webpage
            return render_template('adversary_messages.html', title='Messages', msg_form=msg_form, adv_msg_edit_form=adv_msg_edit_form,
            adv_buttons_form=adv_buttons_form, adv_next_round_form=adv_next_round_form, message=display_message, game=current_game,
            current_msg=(current_game.adv_current_msg+1), msg_list_size=current_game.adv_current_msg_list_size, prev_msgs=prev_msgs, prev_msg_flag=prev_msg_flag)
        
        elif adv_next_round_form.advance_round.data: #if the adversary clicks the advance round button
            #check if there are any messages sent in the current round, this is to prevent the round being accidentally increased, or increased from multiple of the same post requests
            current_round_messages = Message.query.filter_by(round=current_game.current_round+1, game=current_game.id).all()
            if not current_round_messages:
                flash(f'The round cannot be advanced when no messages have been sent.', 'danger')
                return render_template('adversary_messages.html', title='Messages', msg_form=msg_form, adv_msg_edit_form=adv_msg_edit_form,
                adv_buttons_form=adv_buttons_form, adv_next_round_form=adv_next_round_form, message=display_message, game=current_game,
                current_msg=(current_game.adv_current_msg+1), msg_list_size=current_game.adv_current_msg_list_size, prev_msgs=prev_msgs, prev_msg_flag=prev_msg_flag)

            #increment the current_round and reset the current message and current message list size, then commit changes
            current_game.current_round += 1
            current_game.adv_current_msg = 0
            current_game.adv_current_msg_list_size = 0
            db.session.commit()
            #pull the messages again since the messages we want to display has changed
            messages = Message.query.filter_by(round=current_game.current_round+1, game=current_game.id).all()
            current_game.adv_current_msg = 0
            current_game.adv_current_msg_list_size = len(messages)
            db.session.commit()

            if (messages): #if messages has content, set the display message to the adversary's current message
                display_message = messages[current_game.adv_current_msg]

            else: #if there are no messages, set display message to none
                display_message = None

            #render the webpage
            return render_template('adversary_messages.html', title='Messages', msg_form=msg_form, adv_msg_edit_form=adv_msg_edit_form,
            adv_buttons_form=adv_buttons_form, adv_next_round_form=adv_next_round_form, message=display_message, game=current_game,
            current_msg=(current_game.adv_current_msg+1), msg_list_size=current_game.adv_current_msg_list_size, prev_msgs=prev_msgs, prev_msg_flag=prev_msg_flag)
        
        else:
            # display normally
            return render_template('adversary_messages.html', title='Messages', msg_form=msg_form, adv_msg_edit_form=adv_msg_edit_form,
            adv_buttons_form=adv_buttons_form, adv_next_round_form=adv_next_round_form, message=display_message, game=current_game,
            current_msg=(current_game.adv_current_msg+1), msg_list_size=current_game.adv_current_msg_list_size, prev_msgs=prev_msgs, prev_msg_flag=prev_msg_flag)
    
    #for regular users

    #setup the current_game variable so we can pull information from it
    game_id = None
    games = Game.query.filter_by(is_running=True).all() #grab all the running games
    for game in games:
        if check_for_str(game.players, current_user.username): #check if the current_user is in the target game
            game_id = game.id #if they are, set the game_id variable to the found game

    current_game = Game.query.filter_by(id=game_id).first() #select the current_game by id

    form = MessageForm() #use the standard message form
    msgs = None
    if (current_game.current_round>1): 
        #pull messages from current_round where the message isn't deleted
        display_message = Message.query.filter_by(round=current_game.current_round, is_deleted=False, game=current_game.id).all()
        msgs = [] #create a list to store the messages to dispay to pass to the template
        for message in display_message: #for each message
            if check_for_str(message.recipient, current_user.username) or (check_for_str(message.sender, current_user.username) and not message.is_edited):
                #check if one of the recipients or sender is the same as the current user, and append it to the list
                msgs.append(message)
    
    #setup message flag to tell template if it should display messages or not
    msg_flag = True
    if not msgs: #if the list of messages is empty, set the flag to false
        msg_flag = False

    #grab the messages from previous rounds
    prev_msgs = None
    if (current_game.current_round>2): #messages are created with current_round+1, so there shouldn't be a reason to display messages on rounds 1 or 2
        prev_messages = Message.query.filter_by(is_deleted=False, game=current_game.id).all() #grab all the previous messages for this game that aren't deleted
        msg_round = current_game.current_round-1 #create an "iterator" so messages are displayed in order of round
        prev_msgs = []
        while msg_round>=2:
            for message in prev_messages: #there won't be any messages from round 1 because messages are created with current_round+1, so stop at round 2
                if message.round == msg_round: #if the target message matches the round we are parsing this loop
                    if check_for_str(message.recipient, current_user.username) or (check_for_str(message.sender, current_user.username) and not message.is_edited):
                    #check if one of the recipients or sender is the same as the current user, and append it to the list
                        prev_msgs.append(message)
            msg_round -= 1 #decrement iterator

    #setup previous message flag to tell template if it should display previous messages or not
    prev_msg_flag = True
    if not prev_msgs: #if the list of previous messages is empty, set the flag to false
        prev_msg_flag = False
    
    if form.validate_on_submit(): #when the user submits the message form and it is valid
        
        #if recipient or content are None display an error and don't put the message in the db
        if not form.recipient.data or not form.content.data:
            flash(f'There was an error in creating your message. Please try again.', 'danger')
            return render_template('messages.html', title='Messages', form=form, msgs=msgs, game=current_game, msg_flag=msg_flag, prev_msgs=prev_msgs, prev_msg_flag=prev_msg_flag)

        users=[] #make a list to put usernames in for the recipient
        #this creates a string of user objects, maps the whole thing to a string, parses that string for only the usernames,
        #then maps the list of usernames into a string to pass into the db
        recipients = ''.join(map(str, parse_for_username(''.join(map(str, form.recipient.data)), users)))
        
        #if the message is a duplicate display an error and don't put the message in the db
        if Message.query.filter_by(sender=current_user.username, recipient=recipients, content=form.content.data, round=current_game.current_round+1, game=current_game.id).first():
            flash(f'Duplicate message detected. Please try sending a different message.', 'danger')
            return render_template('messages.html', title='Messages', form=form, msgs=msgs, game=current_game, msg_flag=msg_flag, prev_msgs=prev_msgs, prev_msg_flag=prev_msg_flag)

        #prevent the user from creating more than one message per round, flash error message if they try
        if Message.query.filter_by(sender=current_user.username, round=current_game.current_round+1, game=current_game.id).first():
            flash(f'Users may only send one message per round. Please wait until the next round to send another message.', 'danger')
            return render_template('messages.html', title='Messages', form=form, msgs=msgs, game=current_game, msg_flag=msg_flag, prev_msgs=prev_msgs, prev_msg_flag=prev_msg_flag)

        #create the new message. grab the current_round for the round var, current user's username for the sender var,
        #selected user's usernames for the recipient var, and the message content
        new_message = Message(round=current_game.current_round+1, game=current_game.id, sender=current_user.username, recipient=recipients,
        content=form.content.data, is_edited=False, new_sender=None, new_recipient=None, edited_content=None, is_deleted=False)
        db.session.add(new_message) #stage the message
        db.session.commit() #commit the message to the db
        flash(f'Your message has been sent!', 'success') #success message to let user know it worked
    #give the template the vars it needs
    return render_template('messages.html', title='Messages', form=form, msgs=msgs, game=current_game, msg_flag=msg_flag, prev_msgs=prev_msgs, prev_msg_flag=prev_msg_flag)

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

    #msg management
    if is_mng_submit and mng_form.validate(): #when the end game button is pressed and the form is valid
        targets = []
        targets = parse_for_game(''.join(map(str, mng_form.games.data)), targets) #search for the games selected by name
        #in theory, this should be able to end multiple games at once properly, but I haven't tested this
        for target in strip_list_str(targets):
            game = Game.query.filter_by(name=target).first() #find the selected game
            game.is_running = False #change it to not running
            adv = User.query.filter_by(username=game.adversary).first() #find the game's adversary
            adv.game = None #remove the game from the user
            db.session.commit() #commit
            player_list = []
            player_list = parse_for_players(game.players, player_list) #grab a list of players from the game
            for player in player_list:
                user = User.query.filter_by(username=player).first() #find each of the player objects
                user.game = None #remove the game from the user
                db.session.commit() #commit
        flash(f'The game has been ended.', 'success') #show success message upon completion

        #pull the forms again because their information has updated, might not need to do this
        mng_form = GMManageGameForm()
        setup_form = GMSetupGameForm()

    #msg setup
    if is_setup_submit and setup_form.validate(): #when the create game button is pressed and the form is valid
        #capture the list of players from the checkboxes
        checkbox_output_list = request.form.getlist('players')
        checkbox_output_str = ''.join(map(str, checkbox_output_list))
        players = checkbox_output_str[:len(checkbox_output_str)-2] #len-2 is so that the last comma and space is removed from the last username
        
        """ old players capturing, leaving for now
        player_list = []
        players = ''.join(map(str, parse_for_username(''.join(map(str, setup_form.players.data)), player_list))) #make a string of players to put in the db
        """

        #"validation" since I don't know how to use the flaskform validation with a custom form, we call the validation in the setup form
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
        player_list = parse_for_players(players, player_list)
        for player in strip_list_str(player_list): #for each player in the string of players
            user = User.query.filter_by(username=player).first() #grab their user object
            print(user)
            user.game = game.id #set their game to this game
            db.session.commit()
        flash(f'The game ' + setup_form.name.data + ' has been created.', 'success') #flash success message
    
    if is_usr_form and usr_form.validate(): #when the edit user button is pressed and the form is valid
        user = User.query.filter_by(username=usr_form.user.data.username).first() #grab the targeted user
        if user.game: #if the user is in a game
            #show an error message. changing a user's role while they are in a game will break stuff
            flash(f'Unable to change a user\'s role while they are in a game. Please end the game first.', 'danger')
            return render_template('game_setup.html', title='Game Setup', mng_form=mng_form, setup_form=setup_form, usr_form=usr_form)
        if usr_form.role.data == 'adv': #if the selected new role is adversary
            user.role = 3 #update to adversary
        if usr_form.role.data == 'usr': #if the selected new role is user
            user.role = 4 #update to user
        db.session.commit()
        flash(f'The user ' + usr_form.user.data.username + ' has been updated.', 'success') #flash success message
    
    #display webpage normally
    return render_template('game_setup.html', title='Game Setup', mng_form=mng_form, setup_form=setup_form, usr_form=usr_form, usernames=usernames)




"""
#sample route for testing pages
#when you copy this to test a page, make sure to change all instances of "testing"

@app.route('/testing') #this decorator tells the website what to put after the http://<IP>
#@app.route('/testing', methods=['GET', 'POST']) #this is needed if the user is doing to submit forms and things
#@login_required #enforce that the user is logged in
def testing():
    return render_template('testing.html', title='Testing') #this tells the app what html template to use. Title isn't needed

"""
