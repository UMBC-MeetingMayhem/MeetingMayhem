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
    if st == "" or st==None:
        return []
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

def create_message(user, game, request, form, recipients, time_stamp):
    print("---------------\n\n\n\n")
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
        return False,None
    if user.role != 3 and user.role != 4:
        return False,None
    prentendSender = None # if adv pretend as others
    # Code for determining whether entered keys are warning or not
    if request.get("Pretend") != None:
        new_recipients = request.get("Pretend")
        prentendSender =  new_recipients
    else:
        prentendSender =  user.username
        
    encryption_type = request.get("encryption_type_select")
    encrypted_key = request.get("encryption_key")
    initial_help_message = ""
    initial_is_cyptographic = 0
    print(encryption_type,encrypted_key)
    if  encryption_type == 'symmetric':
        initial_is_cyptographic = 1
        if recipients in encrypted_key:
            initial_help_message = "Looks Good =)"
        else:
            initial_help_message = 'Warning: Recipient cannot decrypt the message with this key.'
    elif encryption_type  == 'asymmetric':
        initial_is_cyptographic = 2
        if encrypted_key == 'public_' + recipients:
            initial_help_message = "Looks Good =)"
        elif encrypted_key == 'private_' + str(user.username):
            initial_help_message = 'Warning: ' + encrypted_key + " but an asymmetric encryption usually encrypts with the receiver's public key."
        else:
           initial_help_message = 'Warning: Recipient cannot decrypt the message with this key.'
    elif encryption_type  == 'signed':
        initial_is_cyptographic = 3
        if encrypted_key == 'private_' + str(user.username):
            initial_help_message = "Looks Good =)"
        elif encrypted_key == 'public_' + recipients:
            initial_help_message = 'Warning: ' + encrypted_key + " but a signature usually requires the sender's private key."
        else:
            initial_help_message = 'Warning: Recipient cannot decrypt the message with this key.'

    #create the message and add it to the db
    new_message = Message(
                            round=game.current_round+1, game=game.id, 
                            # Initial Content
                            time_sent=time_stamp, time_meet=form.meet_time.data, location_meet=form.meet_location.data, time_am_pm=form.meet_am_pm.data,
                            initial_sender=user.username, initial_recipient=recipients, initial_content=form.content.data, 
                            adv_created= (user.role==3) , 
                            initial_is_cyptographic = initial_is_cyptographic,
                            initial_encryption_type=encryption_type, initial_key = encrypted_key, 
                            initial_help_message = initial_help_message,
                            # Edited content (kept as same as initial, but not processed)
                            adv_processed = (user.role==3) , is_edited=False, is_deleted=False, 
                            edited_sender=prentendSender, edited_recipient=recipients, edited_content=form.content.data, 
                            edited_is_cyptographic = initial_is_cyptographic,
                            edited_encryption_type=encryption_type, edited_key = encrypted_key, 
                            edited_help_message = initial_help_message,
                            # Decrypted
                            is_decryptable=False,has_been_decrypted = False
                            )
    db.session.add(new_message)
    db.session.commit()
    #display success to user
    flash(f'Your message has been sent!', 'success')
    return True, new_message
    


def decrypt_button_show(message):
    """Decides if decrypt button will show
    Args:
        user(User): the current_user object of the user creating a message.
        encryption_keys(Message): the encryption keys associated with a message
        is_encrypted(Message): a boolean value that determines if message is encrypted or not.
    Returns:
        bool: whether or not decrypt button will show
    """
    if message.is_encrypted == False and message.is_signed == False:
        return False
    # Case 1: shared key
    recipient = message.new_recipient if message.new_recipient else message.recipient
    if message.encryption_type == "symmetric" and recipient in message.key: 
        show_result = True
    elif message.encryption_type == "asymmetric" and "private" in message.key:
        show_result = True
    elif message.encryption_type == "asymmetric" and recipient in message.key:
        show_result = True
    # Case 3: Use sender private key, sign
    elif  message.encryption_type == "signed" and "private" in message.key:
        show_result = True
    # Case 4: Use adv_public key, sign
    elif  message.encryption_type == "signed" and recipient in message.key:
        show_result = True
    else:
        show_result = False

    return show_result

def decrypt_button_show_for_adv(message, adv_name):
    # Case 1: Use sender_adv_symmetric key
    if message.initial_encryption_type == "symmetric" and adv_name in message.initial_key:
        message.is_decryptable = True
    # Case 2: Use adv_public key, asymmetric
    elif message.initial_encryption_type == "asymmetric" and adv_name in message.initial_key:
        message.is_decryptable = True
    # Case 3: Use sender private key, asymmetric
    elif message.initial_encryption_type == "asymmetric" and "private" in message.initial_key:
        message.is_decryptable = True
    # Case 3: Use sender private key, sign
    elif  message.initial_encryption_type == "signed" and "private" in message.initial_key:
        message.is_decryptable = True
    # Case 4: Use adv_public key, sign
    elif  message.initial_encryption_type == "signed" and adv_name in message.initial_key:
        message.is_decryptable = True
    else:
        message.is_decryptable = False
    db.session.commit()
