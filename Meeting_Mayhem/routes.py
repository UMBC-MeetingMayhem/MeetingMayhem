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
from Meeting_Mayhem import app, db, bcrypt
from Meeting_Mayhem.forms import RegistrationForm, LoginForm, MessageForm, AdversaryMessageEditForm, AdversaryMessageSubmitForm, AdversaryAdvanceRoundForm, AdversaryMessageSendForm
from Meeting_Mayhem.models import User, Message, Metadata
from flask_login import login_user, current_user, logout_user, login_required

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
    current_game = Metadata.query.filter_by(adversary='adversary').first()
    if form.advance_round.data:
        current_game.current_round -= 1
        current_game.adv_current_msg = 0
        current_game.adv_current_msg_list_size = 0
        db.session.commit()
    return render_template('account.html', title='Account', form=form, role=User.query.filter_by(username=current_user.username).first().role)

#message page
@app.route('/messages', methods=['GET', 'POST']) #POST is enabled here so that users can give the website information to create messages with
@login_required
def messages():
    #set the display_message to None initially so that if there is no message to display it doesn't break the website
    display_message = None

    #TODO: these few lines need to be changed when we can put users into a game instance, it should search dynamically for the game
    #since there is only one adversary and one instance of the game this will work for now
    #if (not (Metadata.query.filter_by(adversary=current_user.username).first())):
    if (not (Metadata.query.filter_by(adversary='adversary').first())): #if there isn't a game with the adversary user as the adversary...
        #create a new game and add it to the database
        new_game = Metadata(adversary=current_user.username, current_round=1, adv_current_msg=0, adv_current_msg_list_size=0)
        db.session.add(new_game)
        db.session.commit()

    #setup the current_game variable so that we can pull game state information from it
    #TODO: this needs to be changed once game instances are implemented, should be dynamic
    current_game = Metadata.query.filter_by(adversary='adversary').first()

    #if the current_user is of the adversary role, then display the adversary version of the page
    if (current_user.role==3):

        #setup variables for the forms the adversary needs to use
        msg_form = AdversaryMessageSendForm()
        adv_msg_edit_form = AdversaryMessageEditForm()
        adv_buttons_form = AdversaryMessageSubmitForm()
        adv_next_round_form = AdversaryAdvanceRoundForm()

        #setup variable to contain the messages that are in the current_round of this game
        messages = Message.query.filter_by(round=current_game.current_round).all()
        
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

        if msg_form.submit.data and msg_form.validate(): #if the adversary tries to send a message, and it is valid

            #create the new message variable with the information from the form
            new_message = Message(round=(current_game.current_round+1), sender=msg_form.sender.data.username,
            recipient=msg_form.recipient.data.username, content=msg_form.content.data, is_edited=True, new_sender=None,
            new_recipient=None, edited_content=None)

            db.session.add(new_message) #stage the message
            db.session.commit() #commit the message to the db
            flash(f'Your message has been sent!', 'success') #success message to let user know it worked

            #render the webpage
            return render_template('adversary_messages.html', title='Messages', msg_form=msg_form, adv_msg_edit_form=adv_msg_edit_form,
            adv_buttons_form=adv_buttons_form, adv_next_round_form=adv_next_round_form, message=display_message, game=current_game,
            current_msg=current_game.adv_current_msg, msg_list_size=current_game.adv_current_msg_list_size)
        
        elif ((is_prev_submit or is_next_submit or is_submit_edits)): #if any of the prev/next/submit buttons are clicked
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
            
            #TODO: some sort of validation here?
            elif is_submit_edits: #if the submit button is clicked
                #setup the changes to be made to the current message
                display_message.round = display_message.round+1
                display_message.is_edited = True
                display_message.new_sender = adv_msg_edit_form.new_sender.data.username
                display_message.new_recipient = adv_msg_edit_form.new_recipient.data.username
                display_message.edited_content = adv_msg_edit_form.edited_content.data
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

            #render the webpage
            return render_template('adversary_messages.html', title='Messages', msg_form=msg_form, adv_msg_edit_form=adv_msg_edit_form,
            adv_buttons_form=adv_buttons_form, adv_next_round_form=adv_next_round_form, message=display_message, game=current_game,
            current_msg=(current_game.adv_current_msg+1), msg_list_size=current_game.adv_current_msg_list_size)
        
        elif adv_next_round_form.advance_round.data: #if the adversary clicks the advance round button
            #increment the current_round and reset the current message and current message list size, then commit changes
            current_game.current_round += 1
            current_game.adv_current_msg = 0
            current_game.adv_current_msg_list_size = 0
            db.session.commit()

            #render the webpage
            return render_template('adversary_messages.html', title='Messages', msg_form=msg_form, adv_msg_edit_form=adv_msg_edit_form,
            adv_buttons_form=adv_buttons_form, adv_next_round_form=adv_next_round_form, message=display_message, game=current_game,
            current_msg=current_game.adv_current_msg, msg_list_size=current_game.adv_current_msg_list_size)
        
        else:
            # display normally
            return render_template('adversary_messages.html', title='Messages', msg_form=msg_form, adv_msg_edit_form=adv_msg_edit_form,
            adv_buttons_form=adv_buttons_form, adv_next_round_form=adv_next_round_form, message=display_message, game=current_game,
            current_msg=current_game.adv_current_msg, msg_list_size=current_game.adv_current_msg_list_size)
    
    #for all other users
    form = MessageForm() #use the message form
    if (current_game.current_round>1): 
        #pull messages from current_round-1 where the current user is the recipient
        display_message = Message.query.filter_by(round=current_game.current_round-1).filter_by(recipient=current_user.username)
    if form.validate_on_submit(): #when the user submits the message form and it is valid
        #create the new message. grab the current_round for the round var, current user's username for the sender var,
        #dropdown selected user's username for the recipient var, and the message content
        new_message = Message(round=current_game.current_round, sender=current_user.username, recipient=form.recipient.data.username,
        content=form.content.data, is_edited=False, new_sender=None, new_recipient=None, edited_content=None)
        db.session.add(new_message) #stage the message
        db.session.commit() #commit the message to the db
        flash(f'Your message has been sent!', 'success') #success message to let user know it worked
    #give the template the vars it needs
    return render_template('messages.html', title='Messages', form=form, message=display_message)