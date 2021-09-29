"""
File: helper.py
Author: Robert Shovan /Voitheia
Date Created: 8/10/2021
Last Modified: 9/6/2021
E-mail: rshovan1@umbc.edu
Description: python file that contains helper functions for other python files.
Docstring info: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
"""
from flask import flash
from MeetingMayhem import db
from MeetingMayhem.models import Message

#recursivley parse the given string for usernames, return true if the given username is found
def check_for_str(str, check):
    """Recursivley parse a string for usernames to find the username passed.

    This is used to detect when a user is a recipient of a message.

    Args:
        str (str): the string that contains usernames
        check (str): the username we are looking for

    Returns:
        bool: True if the username we are looking for is found.
    
    Todo:
        Rename check to something better.
    """
    if str: #check if the passed string is empty or not
        str1=str.partition(', ') #split the string into the username, the "', ", and the rest of the string
        if (str1[0] == check): #if the first part of str is the username we are looking for
            return True
        if (not str1[2]): #if there is nothing in the rest of str, it means there are no more usernames to look for
            return False
        else:
            return check_for_str(str1[2], check) #call this method again if there is more string to look through
    else: #if the passed string is empty, return false
        return False

#used to strip commas and white spaces out of lists of strings
def strip_list_str(str_list):
    """Parse a list of strings, and remove and commas or white spaces after the text we want.

    This is used by the game_seutp page to clean up lists of usernames and game names.

    Args:
        str_list (list): the list that we want to clean up
    
    Returns:
        list: the same list of players that was passed as an argument with commas and white space removed from the end of the string.
    """
    if str_list: #check if the passed list is empty or not
        new_str_list = []
        for str in str_list:
            new_str = str.partition(",")[0] #put everything before the comma into the new list
            new_str_list.append(new_str)
        return new_str_list
    else:
        return str_list #if the passed list is empty return the list

def str_to_list(st, li):
    """Recursivley parse a string delimited by ", " and put the separate strings into a list

    This is used in game validation when detecting players that are already in a game, and by
    the game_setup page for pulling usernames out of the players field of a game.

    Args:
        st (str): a string delimited by ", " which we want to make into a list.
        li (list): an empty list where we will put the list of strings.
    
    Returns:
        list: the same list that was passed as an argument, now filled with strings.

    Throws:
        TypeError: when incorrect argument type or empty string is passed to function.
    """
    #check if the passed arguments are the correct type, and string isn't empty
    if isinstance(st, str) and isinstance(li, list) and st:
        li.append(st.partition(', ')[0]) #append the first part of the string to the list
        new_st = st.partition(', ')[2] #capture the rest of the string and put it in a new str
        if new_st: #if the new str has content
            str_to_list(new_st, li) #call this function again with new str and same list
    else:
        #raise an exception
        raise TypeError("Incorrect argument type or empty string passed to function.")
    return li #return the list filled with strings

def create_message(user, game, request, form):
    """Create a message. Used by both the adversary and the users.

    Intention is to use this function with a switch statement so that different actions can
    be taking depending on which code is returned.

    Args:
        user(User): the current_user object of the user creating a message.
        game(Game): the current_game object from the instance that is calling this function.
        request(request.form): the request form that contains checkbox stuff.
        form(form/msg_form): the form from the website that contains msg content

    Returns:
        bool: whether or not the message sent successfully
    """
    if not form.content.data: #if there is no message content, display an error, return false
        flash(f'There was an error in creating your message. Please try again.', 'danger')
        return False
    if user.role == 3: #if the user is an adversary
        #get the list of the recipients and senders
        checkbox_output_list_recipients = request.getlist('recipients')
        checkbox_output_list_senders = request.getlist('senders')
        #if one of those lists are empty, display an error, return false
        if not checkbox_output_list_recipients or not checkbox_output_list_senders:
            flash(f'Please select at least one sender and one recipient.', 'danger')
            return False
        #make the lists into strings
        checkbox_output_str_recipients = ''.join(map(str, checkbox_output_list_recipients))
        checkbox_output_str_senders = ''.join(map(str, checkbox_output_list_senders))
        #remove the last ', ' off of the strings
        recipients = checkbox_output_str_recipients[:len(checkbox_output_str_recipients)-2]
        senders = checkbox_output_str_senders[:len(checkbox_output_str_senders)-2]
        #check if the message is a duplicate, and if it is, display an error, return false
        if Message.query.filter_by(sender=senders, recipient=recipients, content=form.content.data, round=game.current_round+1, game=game.id).first():
            flash(f'Duplicate message detected. Please try sending a different message.', 'danger')
            return False
        #create the message and add it to the db
        new_message = Message(round=game.current_round+1, game=game.id, sender=senders, recipient=recipients, content=form.content.data, is_edited=False, new_sender=None, new_recipient=None, edited_content=None, is_deleted=False, adv_created=True, is_encrypted=False, is_signed=False)
        db.session.add(new_message)
        db.session.commit()
        #display success to user
        flash(f'Your message has been sent!', 'success')
        return True
    elif user.role == 4: #if the user is a user
        #get the list of recipients
        checkbox_output_list = request.getlist('recipients')
        #if that list is empty, display an error, return false
        if not checkbox_output_list:
            flash(f'There was an error in creating your message. Please try again.', 'danger')
            return False
        #make the list into a string
        checkbox_output_str = ''.join(map(str, checkbox_output_list))
        #remove the last ', ' off the string
        recipients = checkbox_output_str[:len(checkbox_output_str)-2]
        #check if the message is a duplicate, and if it is, display an error, return false
        encryption_output = request.get('encryption_and_signed_keys')
        signed_keys = [] # list to keep track of digital signatures
        encrypted_keys = [] # list to keep track of encryption keys
        #check if the message is a duplicate, and if it is, display an error, return false
        if Message.query.filter_by(sender=user.username, recipient=recipients, content=form.content.data, round=game.current_round+1, game=game.id).first():
            flash(f'Please select at least one sender and one recipient.', 'danger')
            return False
        #check if the user has already sent a message this round, and if they have, display an error, return false
        if Message.query.filter_by(sender=user.username, round=game.current_round+1, game=game.id).first():
            flash(f'Users may only send one message per round. Please wait until the next round to send another message.', 'danger')
            return False
        for element in encryption_output.split(','):
            if element.split('(')[0] == 'Sign':
                signed_keys.append(element.split('(')[1][0:len(element.split('(')[1]) - 1])
            else:
                encrypted_keys.append(element.split('(')[1][0:len(element.split('(')[1]) - 1])
        signed_keys_string = ','.join(map(str, signed_keys))
        encrypted_keys_string = ','.join(map(str, encrypted_keys))
        
        #create the message and add it to the db
        new_message = Message(round=game.current_round+1, game=game.id, sender=user.username, recipient=recipients, content=form.content.data, is_edited=False, new_sender=None, new_recipient=None, edited_content=None, is_deleted=False, adv_created=False, is_encrypted=(len(encrypted_keys)> 0), encryption_details = encrypted_keys_string, is_signed = (len(signed_keys) > 0), signed_details = signed_keys_string)
        
        db.session.add(new_message)
        db.session.commit()
        #display success to user
        flash(f'Your message has been sent!', 'success')
        return True
    else: #if someone who isn't a user or adversary manages to call this function, return false
        return False