"""
File: helper.py
Author: Robert Shovan /Voitheia
Date Created: 8/10/2021
Last Modified: 9/6/2021
E-mail: rshovan1@umbc.edu
Description: python file that contains helper functions for other python files.
Docstring info: https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
"""

def parse_for_name(st, names):
    """Recursivley parse a string filled with a lot of junk for names, intended to be either usernames or game names.
    
    This is used in creating a string of usernames for both message creation and game creation.
    Also used in game validation when detecting players that are already in a game.
    Also used by the game_seutp page for pulling games out of the QuerySelectMultipleField.

    Args:
        st (str): a string output of the website which has names in it.
        names (list): an empty list where we will put the names we find in st.
    
    Returns:
        list: the same list that was passed as an argument, now filled with names.

    Throws:
        TypeError: when incorrect argument type or empty string is passed to function.
    """
    #check if the passed arguments are the correct type, and string isn't empty
    if isinstance(st, str) and isinstance(names, list) and st:
        """this removes the first part of the string, before the username or game. its really gross because in order to work
        for both usernames and game names, "name='" needs to be searched for, but "ame='" won't work because "Game='" will
        also appear, so we need to make st lowercase because we need to find both "name='" and "Name='", but we don't want
        to remove the lowercase from the string when we save it to st_front, so I ended up with this thing. it basically
        finds the index of where the name starts, and then sets st_front to start at that index."""
        st_front = st[len(st)-len(st.lower().partition("name='")[2]):]
        st_back = st_front.partition("', ") #create a partition where "', " is found next
        if st_back[2]:
            if (st_back[2].lower().find("name='") != -1): #if there is another name
                name = st_back[0] + ', ' #append ', ' to the name we just found
                names.append(name) #and add it to the list
                parse_for_name(st_back[2], names) #and call this method again with the rest of the string
            else:
                names.append(st_back[0]) #if not, just append the name without the ', ' and then return
    else:
        #raise an exception
        raise TypeError("Incorrect argument type or empty string passed to function.")
    return names #return the list filled with names

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

"""replaced by str_to_list
#recursivley parse the given string for players, return a list of players used for resetting a player's game when the game is ended
def parse_for_players(str, players):
    Recursivley parse a given string for player's usernames using .partition to select usernames.

    This is used by the game_seutp page for pulling usernames out of the players field of a game.

    Args:
        str (str): the string that contains the players
        players (list): the list of players to be filled out
    
    Returns:
        list: the same list of players that was passed as an argument, filled out with any usernames found.

    Todo:
        Explore combining this function with usernames_to_str_list since they do similar things.
    
    if str: #check if the passed string is empty or not
        players.append(str.partition(', ')[0])
        str1=str.partition(', ')[2]
        if str1:
            parse_for_players(str1, players)
    return players #return the list of players
"""

"""replaced by str_to_list
#recursivley check a string with multiple usernames in it for usernames, and put them in a list
def usernames_to_str_list(usernames, username_list):
    Recursivley parse a string with multiple usernames in it, and append them to a list.

    This is used in game validation when detecting players that are already in a game.

    Args:
        usernames (str): a string of usernames delimited by commas we want to make into a list
        username_list (list): an empty list where we will put the usernames

    Returns:
        list: the same list of usernames that was passed as an argument, now filled with usernames that were in the passed username string.
    
    Todo:
        Explore combining this function with parse_for_players since they do similar things.
    
    if usernames: #check if usernames is empty or not
        username_list.append(usernames.partition(', ')[0]) #put the first username into the list
        new_usernames = usernames.partition(', ')[2] #grab the rest of the string
        if new_usernames: #if there are still usernames to parse
            username_list = usernames_to_str_list(new_usernames, username_list) #call this method again with the new string
    return username_list #return the list
"""

"""more old stuff
#recursivley parse the given string for usernames, return a list of usernames delimited by commas
def parse_for_username(str, users):
    Recursivley parse a given string for usernames using .partition to select usernames.

    This is used in creating a string of usernames for both message creation and game creation.
    Also used in game validation when detecting players that are already in a game.

    Args:
        str (str): the string that contains the usernames
        users (list): the list of usernames to be filled out
    
    Returns:
        list: the same list of users that was passed as an argument, filled out with any usernames found.
    
    Todo:
        Explore combining this function with parse_for_game since they do almost the same thing. Would need to specify what is being looked for.
    
    if str: #check if the passed string is empty or not
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

#same thing as the parse_for_username function, just for games instead
def parse_for_game(str, games):
    Recursivley parse a given string for names of games using .partition to select game names.

    This is used by the game_seutp page for pulling games out of the QuerySelectMultipleField.

    Args:
        str (str): the string that contains games
        games (list): the list of games to be filled out
    
    Returns:
        list: the same list of games that was passed as an argument, filled out with any games found in the passed string.
    
    Todo:
        Explore combining this function with parse_for_username since they do almost the same thing. Would need to specify what is being looked for.
    
    if str: #check if the passed string is empty or not
        str1=str.partition("Name='")[2]
        str2=str1.partition("', ")
        if str2[2]:
            if (str2[2].find('Name') != -1):
                game = str2[0] + ', '
                games.append(game)
                parse_for_game(str2[2], games)
            else:
                games.append(str2[0])
    return games #return the list of games
"""