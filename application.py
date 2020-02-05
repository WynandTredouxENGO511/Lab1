"""
Environemnt variables
DATABASE_URL=postgres://qbtxfingwrqmyc:962e9c32a97ff8eb6dff5e85a07032b9a9758d9da76c231864487642df21726a@ec2-35-168-54-239.compute-1.amazonaws.com:5432/d3tu5tucael6mf
"""

import os

from flask import Flask, session, request, render_template
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)


# Check for DATABASE_URL variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Load config
app.config.from_pyfile('config.cfg', silent=True) #load settings from config.cfg
Session(app)

# Set up database
engine = create_engine('postgres://qbtxfingwrqmyc:962e9c32a97ff8eb6dff5e85a07032b9a9758d9da76c231864487642df21726a@ec2-35-168-54-239.compute-1.amazonaws.com:5432/d3tu5tucael6mf')
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def home():
    return render_template('home.html')

@app.route("/login")
def login():
    return render_template('login.html')

if __name__ == '__main__':
    app.run()