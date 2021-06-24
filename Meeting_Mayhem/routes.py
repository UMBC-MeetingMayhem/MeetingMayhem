"""
File: routes.py
Author: Robert Shovan /Voitheia
Date Created: 6/15/2021
Last Modified: 6/24/2021
E-mail: rshovan1@umbc.edu
Description: python file that handles the routes for the website.
"""

"""
info about imports
render_template - used for giving the website the final html page with the layout and passed page
url_for - used to resolve the url for the passed string
flash - used for alerts sent to the user
redirect - used to redirect the user to a different page when something happens
request - used to see if there is a next_page argument in the url so the user can be redirected there upon login
app, db, bcrypt - import the app, database, and encryption functionality from the package we initialized in the __init__.py file
forms - import the forms we created in the forms.py file
User, Packet - imports the User and Packet models so we can make users and packets
flask_login - different utilities used for loggin the user in, seeing which user is logged in, logging the user out, and requireing login for a page
"""
from flask import render_template, url_for, flash, redirect, request
from Meeting_Mayhem import app, db, bcrypt
from Meeting_Mayhem.forms import RegistrationForm, LoginForm, PacketForm
from Meeting_Mayhem.models import User, Packet
from flask_login import login_user, current_user, logout_user, login_required

#root route, basically the homepage, this page doesn't really do anything right now
#having two routes means that flask will put the same html on both of those pages
#by using the render_template, we are able to pass an html document to flask for it to put on the web server
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', title='Home')

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
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8') #this hashes the user's password and converts it to utf-8
        user = User(username=form.username.data, email=form.email.data, password=hashed_password) #create the user for the db
        db.session.add(user) #stage the user for the db
        db.session.commit() #commit new user to db
        flash(f'Your account has been created! Please login', 'success')
        return redirect(url_for('login')) #redir the user to the login page
    return render_template('register.html', title='Register', form=form)

#login page route
@app.route('/login', methods=['GET', 'POST']) #POST is enabled here so that users can give the website information to login with
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home')) #if the user is logged in, redir to home
    form = LoginForm() #specify which form to use
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first() #check that the user exists, using email because that's what the user uses to log in
        if user and bcrypt.check_password_hash(user.password, form.password.data): #if the user exists and the password is correct
            login_user(user, remember=form.remember.data) #log the user in, and if the user checked the remeber box, remember the user
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

#account page route, this page just displays the current user's username for dev purposes
@app.route('/account')
@login_required #enforces that the the user needs to be logged in if they navigate to this page
def account():
    return render_template('account.html', title='Account')

#packet page
#current_round probably starts at 1 for now, gets advanced when a player send a packet
#TODO: make current_round advance automatically, this will be done by the adversary's actions eventually
#this will be changed later when we add the adversary, as their submit will advance the round counter
current_round = 2 #keeps track of what round it is so the page knows which packets to display
@app.route('/packets', methods=['GET', 'POST']) #POST is enabled here so that users can give the website information to create packets with
@login_required
def packets():
    form = PacketForm() #use the packet form
    display_packet = None #set the display_packet to None initially so that if there is no packet to display it doesn't break the website
    if (current_round>1): 
        #pull packets from current_round-1 where the current user is the recipient
        display_packet = Packet.query.filter_by(round=current_round-1).filter_by(recipient=current_user.username)
    if form.validate_on_submit(): #when the user submits the packet form and it is valid
        #create the new packet. grab the current_round for the round var, current user's username for the sender var, dropdown selected user's username for the recipient var, and the message content
        new_packet = Packet(round=current_round, sender=current_user.username, recipient=form.recipient.data.username, content=form.content.data)
        db.session.add(new_packet) #stage the packet
        db.session.commit() #commit the packet to the db
        flash(f'Your packet has been sent!', 'success') #success message to let user know it worked
    return render_template('packets.html', title='Packets', form=form, packet=display_packet) #give the template the vars it needs
