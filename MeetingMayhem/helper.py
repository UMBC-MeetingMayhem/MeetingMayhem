"""
File: helper.py
Author: Robert Shovan /Voitheia
Date Created: 8/10/2021
Last Modified: 9/6/2021
E-mail: rshovan1@umbc.edu
Description: python file that contains helper functions for other python files.
Docstring info: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
"""

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