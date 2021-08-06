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
from MeetingMayhem import app, db, bcrypt
from MeetingMayhem.forms import GMManageUserForm, RegistrationForm, LoginForm, MessageForm, AdversaryMessageEditForm, AdversaryMessageButtonForm, AdversaryAdvanceRoundForm, AdversaryMessageSendForm, GMManageGameForm, GMSetupGameForm
from MeetingMayhem.models import User, Message, Game
from flask_login import login_user, logout_user, login_required, current_user

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

def strip_list_str(str_list):
    new_str_list = []
    for str in str_list:
        new_str = str.partition(",")[0]
        new_str_list.append(new_str)
    return new_str_list

"""
def username_str_to_list(usernames):
    username_list = []
    username_list.append(usernames.partition(',')[0])
    new_usernames = usernames.partition(',')[2]
    if new_usernames:
        username_to_str_list_rec(new_usernames, username_list)
    return username_list
"""
"""
def username_to_str_list(usernames, username_list):
    print('start')
    print(usernames)
    print(username_list)
    username_list.append(usernames.partition(',')[0])
    new_usernames = usernames.partition(',')[2]
    print(new_usernames)
    print(username_list)
    if new_usernames:
        username_list = username_to_str_list(new_usernames, username_list)
        print(username_list)
        print('if')
    return username_list
"""

#root route, basically the homepage, this page doesn't really do anything right now
#having two routes means that flask will put the same html on both of those pages
#by using the render_template, we are able to pass an html document to flask for it to put on the web server
@app.route('/') #this line states that if the user tries to access http:/<IP>:5000/ it will use the home funciton
@app.route('/home') #likewise, this line is for http:/<IP>:5000/home
def home():
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
        flash(f'Your account has been created! Please login', 'success') #flash a success message to let the user know the account was made
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
            return redirect(next_page) if next_page else redirect(url_for('home')) #redir the user to the next_page arg if it exists, if not send them to home page
        else:
            flash(f'Login Unsuccessful. Please check username and password.', 'danger') #display error message
    return render_template('login.html', title='Login', form=form)

#logout route
@app.route('/logout')
def logout():
    logout_user() #logout user
    return redirect(url_for('home')) #redir the user to the home page

#account page route, this page has the user's username and areas for stats and account information when that gets implemented
@app.route('/account', methods=['GET', 'POST']) #, methods=['GET', 'POST']) needs to be removed when the decrement round button is
@login_required #enforces that the the user needs to be logged in if they navigate to this page
def account():
    #create a button in the account page that can decrement the round for testing purposes, will only be displayed for adversary user
    form = AdversaryAdvanceRoundForm()
    current_game = Game.query.filter_by(adversary=current_user.username).first()
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

    if not current_user.game: #if the current user isn't in a game, send them to the homepage
        flash(f'You are not currently in a game. Please have your game master put you in a game.', 'danger')
        return render_template('home.html', title='Home')

    #set the display_message to None initially so that if there is no message to display it doesn't break the website
    display_message = None

    """

    #TODO: these few lines need to be changed when we can put users into a game instance, it should search dynamically for the game
    #since there is only one adversary and one instance of the game this will work for now
    #if (not (Game.query.filter_by(adversary=current_user.username).first())):
    if (not (Game.query.filter_by(adversary='adversary').first())): #if there isn't a game with the adversary user as the adversary...
        #create a new game and add it to the database
        new_game = Game(adversary=current_user.username, current_round=1, adv_current_msg=0, adv_current_msg_list_size=0)
        db.session.add(new_game)
        db.session.commit()

    #setup the current_game variable so that we can pull game state information from it
    #TODO: this needs to be changed once game instances are implemented, should be dynamic
    current_game = Game.query.filter_by(adversary='adversary').first()

    """

    #if the current_user is of the game master or adversary role, then display the adversary version of the page
    if (current_user.role==2 or current_user.role==3):

        current_game = Game.query.filter_by(adversary=current_user.username).first()

        #setup variables for the forms the adversary needs to use
        msg_form = AdversaryMessageSendForm()
        adv_msg_edit_form = AdversaryMessageEditForm()
        adv_buttons_form = AdversaryMessageButtonForm()
        adv_next_round_form = AdversaryAdvanceRoundForm()

        #setup variable to contain the messages that are in the current_round of this game
        messages = Message.query.filter_by(round=current_game.current_round+1).all()
        
        if (messages): #if messages has content, set the display message to the adversary's current message
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

        if msg_form.submit.data and msg_form.validate(): #if the adversary tries to send a message, and it is valid

            users_recipients=[] #make a list to put usernames in for the recipient
            users_senders=[] #make a list to put usernames in for the sender
            #this creates a string of user objects, maps the whole thing to a string, parses that string for only the usernames,
            #then maps the list of usernames into a string to pass into the db
            recipients = ''.join(map(str, parse_for_username(''.join(map(str, msg_form.recipient.data)), users_recipients)))
            senders = ''.join(map(str, parse_for_username(''.join(map(str, msg_form.sender.data)), users_senders)))

            #create the new message variable with the information from the form
            new_message = Message(round=(current_game.current_round+1), sender=senders, recipient=recipients, content=msg_form.content.data,
            is_edited=True, new_sender=None, new_recipient=None, edited_content=None, is_deleted=False)

            db.session.add(new_message) #stage the message
            db.session.commit() #commit the message to the db
            flash(f'Your message has been sent!', 'success') #success message to let user know it worked

            #render the webpage
            return render_template('adversary_messages.html', title='Messages', msg_form=msg_form, adv_msg_edit_form=adv_msg_edit_form,
            adv_buttons_form=adv_buttons_form, adv_next_round_form=adv_next_round_form, message=display_message, game=current_game,
            current_msg=(current_game.adv_current_msg+1), msg_list_size=current_game.adv_current_msg_list_size)
        
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
            elif is_submit_edits: #if the submit button is clicked
                users_recipients=[] #make a list to put usernames in for the recipient
                users_senders=[] #make a list to put usernames in for the sender
                #this creates a string of user objects, maps the whole thing to a string, parses that string for only the usernames,
                #then maps the list of usernames into a string to pass into the db
                new_recipients = ''.join(map(str, parse_for_username(''.join(map(str, msg_form.recipient.data)), users_recipients)))
                new_senders = ''.join(map(str, parse_for_username(''.join(map(str, msg_form.sender.data)), users_senders)))
                #setup the changes to be made to the current message
                display_message.is_edited = True
                display_message.new_sender = new_senders
                display_message.new_recipient = new_recipients
                display_message.edited_content = adv_msg_edit_form.edited_content.data
                #pull the messages again since the messages we want to display has changed
                messages = Message.query.filter_by(round=current_game.current_round+1).all()
                current_game.adv_current_msg = 0
                current_game.adv_current_msg_list_size = len(messages)
                #commit the messages to the database
                db.session.commit()

            elif is_delete_msg: #if the delete message button is clicked
                #flag the message as edited and deleted
                display_message.is_edited = True
                display_message.is_deleted = True
                #pull the messages again since the messages we want to display has changed
                messages = Message.query.filter_by(round=current_game.current_round+1).all()
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
            current_msg=(current_game.adv_current_msg+1), msg_list_size=current_game.adv_current_msg_list_size)
        
        elif adv_next_round_form.advance_round.data: #if the adversary clicks the advance round button
            #increment the current_round and reset the current message and current message list size, then commit changes
            current_game.current_round += 1
            current_game.adv_current_msg = 0
            current_game.adv_current_msg_list_size = 0
            #pull the messages again since the messages we want to display has changed
            messages = Message.query.filter_by(round=current_game.current_round+1).all()
            current_game.adv_current_msg = 0
            current_game.adv_current_msg_list_size = len(messages)
            db.session.commit()

            #render the webpage
            return render_template('adversary_messages.html', title='Messages', msg_form=msg_form, adv_msg_edit_form=adv_msg_edit_form,
            adv_buttons_form=adv_buttons_form, adv_next_round_form=adv_next_round_form, message=display_message, game=current_game,
            current_msg=(current_game.adv_current_msg+1), msg_list_size=current_game.adv_current_msg_list_size)
        
        else:
            # display normally
            return render_template('adversary_messages.html', title='Messages', msg_form=msg_form, adv_msg_edit_form=adv_msg_edit_form,
            adv_buttons_form=adv_buttons_form, adv_next_round_form=adv_next_round_form, message=display_message, game=current_game,
            current_msg=(current_game.adv_current_msg+1), msg_list_size=current_game.adv_current_msg_list_size)
    
    #for regular users
    game_id = None
    games = Game.query.filter_by(is_running=True).all()
    for game in games:
        if check_for_str(game.players, current_user.username):
            game_id = game.id

    current_game = Game.query.filter_by(id=game_id).first()

    form = MessageForm() #use the message form
    msgs = None
    if (current_game.current_round>1): 
        #pull messages from current_round where the message isn't deleted
        display_message = Message.query.filter_by(round=current_game.current_round,is_deleted=False).all()

        msgs=[] #create a list to store the messages to dispay to pass to the template
        for message in display_message: #for each message
            if message.recipient: #if the message has a recipient
                if check_for_str(message.recipient, current_user.username):
                    #check if one of the recipients is the same as the current user, and append it to the list
                    msgs.append(message)
        
    if form.validate_on_submit(): #when the user submits the message form and it is valid
        users=[] #make a list to put usernames in for the recipient
        #this creates a string of user objects, maps the whole thing to a string, parses that string for only the usernames,
        #then maps the list of usernames into a string to pass into the db
        recipients = ''.join(map(str, parse_for_username(''.join(map(str, form.recipient.data)), users)))
        
        #create the new message. grab the current_round for the round var, current user's username for the sender var,
        #selected user's usernames for the recipient var, and the message content
        new_message = Message(round=current_game.current_round+1, sender=current_user.username, recipient=recipients,
        content=form.content.data, is_edited=False, new_sender=None, new_recipient=None, edited_content=None, is_deleted=False)
        db.session.add(new_message) #stage the message
        db.session.commit() #commit the message to the db
        flash(f'Your message has been sent!', 'success') #success message to let user know it worked
    #give the template the vars it needs
    return render_template('messages.html', title='Messages', form=form, message=msgs)

# game setup route for the game master
@app.route('/game_setup', methods=['GET', 'POST']) #POST is enabled here so that users can give the website information to create messages with
@login_required #requires the user to be logged in
def game_setup():
    if current_user.role != 2: #if the user isn't a game master
        flash(f'Your permissions are insufficient to access this page.', 'danger')
        return render_template('home.html', title='Home') #display the home page when they try to access this page directly.
    mng_form = GMManageGameForm()
    setup_form = GMSetupGameForm()
    usr_form = GMManageUserForm()

    is_mng_submit = mng_form.end_game.data
    is_setup_submit = setup_form.create_game.data
    is_usr_form = usr_form.update.data

    #msg management
    #TODO: need validation to ensure a game is selected
    if is_mng_submit and mng_form.validate():
        targets = []
        targets = parse_for_game(''.join(map(str, mng_form.games.data)), targets)
        for target in strip_list_str(targets):
            game = Game.query.filter_by(name=target).first()
            game.is_running = False
            #TODO: need to also remove users and adversary from game here
            adv = User.query.filter_by(username=game.adversary).first()
            adv.game = None
            player_list = []
            player_list = parse_for_username(game.players, player_list)
            for player in player_list:
                user = User.query.filter_by(username=player.username)
                user.game = None
            db.session.commit()
        flash(f'The game has been ended.', 'success')
        mng_form = GMManageGameForm()
        setup_form = GMSetupGameForm()

    #msg setup
    #TODO: need validation to ensure players are selected and a name is chosen
    if is_setup_submit and setup_form.validate():
        player_list = []
        players = ''.join(map(str, parse_for_username(''.join(map(str, setup_form.players.data)), player_list)))
        new_game = Game(name=setup_form.name.data, is_running=True, adversary=setup_form.adversary.data.username, players=players, current_round=1, adv_current_msg=0, adv_current_msg_list_size=0)
        db.session.add(new_game)
        db.session.commit()
        #TODO: once the game is created, I need to add the users and adversary to it on their end
        game = Game.query.order_by(-Game.id).filter_by(adversary=setup_form.adversary.data.username,players=players).first() #this finds the last game in the db with the passed players and adversary
        adv = User.query.filter_by(username=setup_form.adversary.data.username).first()
        print(game)
        adv.game=game.id
        for player in strip_list_str(player_list):
            user = User.query.filter_by(username=player).first()
            user.game=game.id
        db.session.commit()
        flash(f'The game ' + setup_form.name.data + ' has been created.', 'success')
    
    if is_usr_form and usr_form.validate():
        user = User.query.filter_by(username=usr_form.user.data.username).first()
        if usr_form.role.data == 'adv':
            user.role = 3
        if usr_form.role.data == 'usr':
            user.role = 4
        db.session.commit()
        flash(f'The user ' + usr_form.user.data.username + ' has been updated.', 'success')
    
    return render_template('game_setup.html', title='Game Setup', mng_form=mng_form, setup_form=setup_form, usr_form=usr_form)




"""
#sample route for testing pages
#when you copy this to test a page, make sure to change all instances of "testing"

@app.route('/testing') #this decorator tells the website what to put after the http://<IP>
#@app.route('/testing', methods=['GET', 'POST']) #this is needed if the user is doing to submit forms and things
#@login_required #enforce that the user is logged in
def testing():
    return render_template('testing.html', title='Testing') #this tells the app what html template to use. Title isn't needed

"""