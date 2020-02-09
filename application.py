"""
Environemnt variables
DATABASE_URL=postgres://qbtxfingwrqmyc:962e9c32a97ff8eb6dff5e85a07032b9a9758d9da76c231864487642df21726a@ec2-35-168-54-239.compute-1.amazonaws.com:5432/d3tu5tucael6mf
"""

import os
import hashlib

from flask import Flask, session, request, render_template, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


# function used to hash user passwords
def encrypt_string(hash_string):
    sha_signature = \
        hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature


app = Flask(__name__)

# Check for DATABASE_URL variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Load config
app.config.from_pyfile('config.cfg', silent=True)  # load settings from config.cfg
Session(app)

# Set up database
engine = create_engine(
    'postgres://qbtxfingwrqmyc:962e9c32a97ff8eb6dff5e85a07032b9a9758d9da76c231864487642df21726a@ec2-35-168-54-239.compute-1.amazonaws.com:5432/d3tu5tucael6mf')
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def home():
    if session.get("user") is None:
        session["user"] = ''
    return render_template('home.html', user=session["user"])


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user") is None:
        session["user"] = ''
    # normal page load
    if request.method == "GET":
        return render_template('login.html', user=session["user"])
    # login/register action
    else:
        username = request.form.get('Username')
        # escape ' character by replacing with ''
        if "'" in username:
            value = username.replace("'", "''")
        password = request.form.get('Password')
        hashpass = encrypt_string(password) # password doesn't need any sanitation since it is hashed
        if 'login' in request.form:
            print('login!')
            # find all users with username
            userswithname = db.execute("SELECT username,password FROM users WHERE username=:u AND password=:p",
                                       {"u": username, "p": hashpass}).fetchall()
            # if username or password doesn't match
            if len(userswithname) == 0:
                return render_template('login.html', logError='Username or password is incorrect', user=session["user"])
            session["user"] = username
            print("login success")
            return redirect(url_for('search'))
        elif 'register' in request.form:
            print('register')
            # check if username is blank
            if username == '':
                return render_template('login.html', regError='Username cannot be blank', user=session["user"])
                # check if password is blank
            if password == '':
                return render_template('login.html', regError='Password cannot be blank', user=session["user"])
            # check if username is already in database
            currentusers = db.execute("SELECT username FROM users").fetchall()
            for user in currentusers:
                if user[0] == username:
                    # reload the page, displaying an error message
                    return render_template('login.html', regError='This username is already taken',
                                           user=session["user"])
            # register the user in the database with a hashed password
            db.execute("INSERT INTO users (username, password) VALUES (:u, :p)",
                       {"u": username, "p": hashpass})
            db.commit()

            print("User {} added ".format(username))
            return render_template('login.html', regComplete=1, user=session["user"])
        print('')

        # reload page
        return render_template('login.html', user=session["user"])


@app.route("/admin")
def admin():
    if session.get("user") is None:
        return redirect(url_for('home'))
    # check for unauthorized access
    if session["user"] != 'admin':
        return redirect(url_for('home'))
    # get all current users
    currentusers = db.execute("SELECT * FROM users").fetchall()
    return render_template('admin.html', user=session["user"], currentusers=currentusers)


@app.route("/logout")
def logout():
    session["user"] = ''
    return redirect(url_for('login'))


@app.route("/search")
def search():
    if session.get("user") is None:
        return redirect(url_for('home'))
    elif session.get("user") == '':
        return redirect(url_for('home'))
    return render_template('search.html', user=session["user"])


if __name__ == '__main__':
    app.run(host='0.0.0.0')
