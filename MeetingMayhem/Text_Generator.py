"""
File: Text_Generator.py
Author: Shan
Date Created: 08/29/2023
E-mail: sh69@illinois.edu
Description: python file that handles AI text generation
"""
from flask import flash
from MeetingMayhem import db
from MeetingMayhem.models import AI_Message
from datetime import datetime, timedelta
import pytz
import random

import openai
from openai.error import OpenAIError
from getpass import getpass
import os
# SIZE limit for generate string
PROCESS_SIZE_LIMIT = 5
MODEL = "pai-001-light-beta3"
MAX_TOKENS = 1024

openai.api_key = 'pk-ReVPlCwdhxggcpIQDKmZXHmOrKSgYbWedRNbtltjJaqLGjxg'
openai.api_base = 'https://api.pawan.krd/pai-001-light-beta/v1'
def create_message_adv(game,form,request):
    """This function is for generating message if adversary created the message

    Args:
        game (class): The current game class
        form (Message_Form): form submitted by user
        request (flsk.request.form): Requst by AI

    Returns:
        flag (Boolean): True if message successfully created
        Message (AI_Message): The message created
    """
    # ERROR Handling
    if not form.content.data: #if there is no message content, display an error, return false
        flash(f'Please fill in content for your form!', 'danger')
        return False,None
    #get the list of the recipients and senders
    recipients = request.get('recipients')
    senders = request.get('senders')
    #print(recipients,senders)
    #if one of those lists are empty, display an error, return false
    if not recipients or not senders:
        flash(f'Please select one sender and one recipient.', 'danger')
        return False,None
    if form.data["meet_time"] == "Time" or form.data["meet_location"] == "Locations":
        flash(f'Please select a time and location.', 'danger')
        return False,None
    if senders == recipients:
        flash(f'Please do not select same sender and recipient!', 'danger')
        return False,None
    
    adv_name = game.adversary
    cryptography_type = request.get("encryption_type_select")
    key = request.get("encryption_key")
    is_encrypted = False
    is_signed = False
    warning_message = ""
    # cryptograph Handling
    if  cryptography_type == 'symmetric':
        is_encrypted = True
        warning_message = key if recipients in key and  adv_name in key\
                    else "Warning: Recipient cannot decrypt the message with this key."
    elif cryptography_type  == 'asymmetric':
        is_encrypted = True
        warning_message = key if key == 'public_' + recipients \
                    else 'Warning: ' + key + " but an asymmetric encryption usually encrypts with the receiver's public key." if "private" in key \
                    else 'Warning: Recipient cannot decrypt the message with this key.'
    elif cryptography_type  == 'signed':
        is_signed = True
        warning_message = key if "private" in key \
                    else 'Warning: ' + key + "but a signature usually requires the sender's private key." if key == 'public_' + recipients \
                    else 'Warning: Recipient cannot decrypt the message with this key.'

    curr_time = datetime.now(pytz.timezone("US/Central")).strftime("%b.%d.%Y-%H.%M")
    time_delay = random.uniform(1.5,3.5)
    recieved_time = datetime.now(pytz.timezone("US/Central")) + timedelta(minutes = time_delay)
    recieved_time = recieved_time.strftime("%b.%d.%Y-%H.%M")
    #create the message and add it to the db
    new_message = AI_Message(
        game = game.id, sender = senders, recipient = recipients, content = form.content.data, time_sent = curr_time, time_recieved = recieved_time, location_meet = form.meet_location.data, time_am_pm = form.meet_am_pm.data, time_meet = form.meet_time.data,
        cryptography_type = cryptography_type, key = key, is_encrypted = is_encrypted, is_signed = is_signed, warning_message = warning_message,
        adv_created = True, is_edited = False, adv_submitted = True,
        new_sender = senders, new_recipient = recipients, 
        is_deleted = False,
        is_decrypted = False
    )
    db.session.add(new_message)
    db.session.commit()
    #display success to user
    flash(f'Your message has been sent!', 'success')
    return True, new_message

def generate_chat_response(logs, model=MODEL, max_tokens = MAX_TOKENS):
    try:
        # Create a completion request with the specified engine, prompt, and max tokens.
        response = openai.ChatCompletion.create(
            model=model,
            max_tokens=max_tokens,
            messages = logs,
            temperature = 0.2
        )
        # return the response text
        return response['choices'][0]['message']['content']

    except OpenAIError as error:
        # Handle API errors.
        error_message = error.__class__.__name__ + ': ' + str(error)
        print('API Error:', error_message)
        return None
    except Exception as e:
        # Handle other exceptions.
        print('Exception:', str(e))
        return None

def generate_conversation_log(sender,recipient,game):
    sent_msg = [message for message in AI_Message.query.filter_by(sender=sender, recipient = recipient, game=game.id).all()]
    #print(sent_msg)
    recieved_msg = [message for message in AI_Message.query.filter_by(new_recipient=sender,new_sender=recipient,adv_submitted=True, is_deleted=False, game=game.id).all()]
    logs = [
        {
            "role": "system", 
            "content": """You are a game player of MeetingMayhem. 
                        MeetingMayhem is a web-based educational game focused on adversarial thinking in the context of network security. In particular, this game gently and non-technically introduces students without prior cybersecurity knowledge to the Dolev-Yao network intruder model. 
                        In MeetingMayhem, three students take on the roles of two agents and an adversary. 
                        Two agents need to agree on a time/location to exchange an essential asset. 
                        The agents communicate through a network controlled by the adversary without knowing the adversary’s identity. 
                        The adversary can insert, block, or modify messages. Students can play different roles, try different strategies, interact with different players, and send different messages. """
        },
        {
            "role": "system", 
            "content" : "You will need to act as agent in the game to reply to any message sent by users"
        },
        {
            "role": "system", 
            "content" : "You want to limit your response to be 1-2 sentence each time and within 50 tokens"
        }

    ]
    # Organize messages by chatbox
    msgs_tuple_list = []
    if recieved_msg:
        for message in recieved_msg:
            msgs_tuple_list.append((message,message.time_recieved))
            db.session.commit()
    if sent_msg:
        for message in sent_msg:
            msgs_tuple_list.append((message, message.time_sent))
            db.session.commit()

    msgs_tuple = sorted(msgs_tuple_list, key=lambda x: datetime.strptime(x[1], "%b.%d.%Y-%H.%M")) 
    for message, _ in msgs_tuple:
        if message.sender == sender:
            logs.append({"role": "assistant", "content": message.content})
        elif message.new_recipient == sender:
            logs.append({"role": "user", "content": message.content})
        else:
            raise Exception("Error for Message")
    return logs

def create_message_agent(game,sender,recipient,content):
    curr_time = datetime.now(pytz.timezone("US/Central")).strftime("%b.%d.%Y-%H.%M")
    location_meet = random.choice(["Cafe", "Track", "Alley", "Dorm", "Garage", "Lab", "Park"])
    time_am_pm = random.choice(["am", "pm"])
    time_meet = random.choice(["1:00", "2:00", "3:00", "4:00", "5:00", "6:00", "7:00", "8:00", "9:00", "10:00", "11:00", "12:00"])
    cryptography_type = ""
    key = ""
    is_encrypted = False
    is_signed = False
    warning_message = ""
    new_message = AI_Message(
        game = game.id, sender = sender, recipient = recipient, content = content, time_sent = curr_time, time_recieved = "", location_meet = location_meet , time_am_pm =time_am_pm , time_meet = time_meet,
        cryptography_type = cryptography_type, key = key, is_encrypted = is_encrypted, is_signed = is_signed, warning_message = warning_message,
        adv_created = False, is_edited = False, adv_submitted = False,
        is_deleted = False,
        is_decrypted = False
    )
    db.session.add(new_message)
    db.session.commit()
    return new_message
def message_generator(game, processed_length, agent_names):
    if processed_length > PROCESS_SIZE_LIMIT:
        return None
    #usernames = agent_names
    #usernames.append(game.adversary)
    # usernames = ["user1","user2","user3"]
    # AI_sender = random.choice(agent_names)
    # AI_recipient = AI_sender
    # while AI_recipient == AI_sender:
    #     AI_recipient = random.choice(usernames)
    AI_sender = "user2"
    AI_recipient = "user3"
    logs = generate_conversation_log(AI_sender,AI_recipient,game)
    print(logs)
    content = generate_chat_response(logs)
    print(content)
    new_message = create_message_agent(game,AI_sender,AI_recipient,content)
    return new_message
    

if __name__ == "__main__":
    example_log = [
        {"role": "user", "content": "How are you doing"}
    ]
    content = generate_chat_response(example_log)
    print(content)
    
    