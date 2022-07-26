"""
Testing Framework: flask_unittest
    -Unfamiliar with pytest
    -Unittest DB mocks seem awful
"""
from os import wait
import flask_unittest as test
import MeetingMayhem.routes as MMroute
from flask import Flask
from flask.testing import FlaskClient
from MeetingMayhem import app as MMapp
from MeetingMayhem import db
from MeetingMayhem.models import User
from random import choices
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from string import ascii_letters, digits
from typing import Any, Tuple  # lazy as hell
from webdriver_manager.chrome import ChromeDriverManager

def insert_user() -> Tuple[str, User]:
    r_name: str = "".join(choices(ascii_letters + digits, k=10))

    user: User = User(
        username=r_name,
        email=f"{r_name}@domain.bruh",
        password="sadkhjgbf",
        role="3"
    )
    db.session.add(user)
    db.session.commit()

    return (r_name, user)

class HomePageViewRouteTests(test.ClientTestCase):
    app: Flask = MMapp

    def home_page_no_login(self, client: FlaskClient) -> None:
        """
        The home page upon the first visit should fit these criteria:
            -Nobody is logged in
            -"Please register for an account or login to proceed." is on the page
        """
        res: Any = client.get("/home")
        self.assertInResponse("Please register for an account or login to proceed.", res)

        return

    def home_page_with_login(self, client: FlaskClient) -> None:
        """
        When a user is logged in, the home page should include their username.
        """
        username, user = insert_user()
        res = None # client.get with some cookie
        self.assertInResponse(username, res)

        return

class LoginPageViewRouteTests(test.ClientTestCase):
    app: Flask = MMapp

    def login_page_blank(self, client: FlaskClient) -> None:
        """
        Upon initial load, the login page should contain two empty fields for username and password.
        """
        res: Any = client.get("/login")
        self.assertInResponse("Username", res)
        self.assertInResponse("Password", res)
        self.assertInResponse("Don't Have An Account?", res)

        return

    def login_page_logged_in(self, client: FlaskClient) -> None:
        return

    def login_page_post_valid(self, client: FlaskClient) -> None:
        return

    def login_page_post_invalid(self, client: FlaskClient) -> None:
        return

class RegisterPageViewRouteTests(test.ClientTestCase):
    app: Flask = MMapp

    def register_page_blank(self, client: FlaskClient) -> None:
        """
        Upon initial load, the register page should contain several empty fields:
        Username, Email, Password, Confirm Password
        """
        res: Any = client.get("/register")
        self.assertInResponse("Username", res)
        self.assertInResponse("Email", res)
        self.assertInResponse("Password", res)
        self.assertInResponse("Confirm Password", res)

        return

    def register_page_post_valid(self, client: FlaskClient) -> None:
        return

    def register_page_post_invalid(self, client: FlaskClient) -> None:
        return








