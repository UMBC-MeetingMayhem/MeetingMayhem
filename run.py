"""
File: run.py
Author: Robert Shovan /Voitheia
Date Created: 6/15/2021
Last Modified: 7/16/2021
E-mail: rshovan1@umbc.edu
Description: python file responsible for running the Meeting Mayhem website/package

Initially, this project was largley based on the tutorial video series:
https://www.youtube.com/watch?v=MwZwr5Tvyxo&list=PL-osiE80TeTs4UjLw5MM6OjgkjFeUxCYH
"""

#import the app from the package so that we can run it here
from MeetingMayhem import app

"""
Runs the app. For now, the app is run in debug mode for ease of development. This allows us to see changes we make to
the website without restarting the server. This will need to change in the future
"""
#this is a change
#this is another change
if __name__ == '__main__':
    #app.run(debug=True) #use this one for local testing
    app.run(debug=True,host="0.0.0.0") #use this one to host for other computers
