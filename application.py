"""
Environemnt variables
DATABASE_URL=postgres://qbtxfingwrqmyc:962e9c32a97ff8eb6dff5e85a07032b9a9758d9da76c231864487642df21726a@ec2-35-168-54-239.compute-1.amazonaws.com:5432/d3tu5tucael6mf
"""

import os
import hashlib

from flask import Flask, session, request, render_template, redirect, url_for, abort
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


# function used to hash user passwords
def encrypt_string(hash_string):
    sha_signature = \
        hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature


# function to deal with quotes in SQL queries
def SQLquotes(str):
    if "'" in str:
        return str.replace("'", "''")
    else:
        return str


app = Flask(__name__)

# Check for DATABASE_URL variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Load config
app.config.from_pyfile('config.cfg', silent=True)  # load settings from config.cfg
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def home():
    if session.get("user") is None:  # initialize user to empty
        session["user"] = ''
    return render_template('home.html', user=session["user"])


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user") is None:  # initialize user to empty
        session["user"] = ''
    # normal page load
    if request.method == "GET":
        return render_template('login.html', user=session["user"])

    # login/register action
    else:
        # get username and password for the login or registration forms
        username = request.form.get('Username')
        # escape ' character by replacing with ''
        username = SQLquotes(username)
        password = request.form.get('Password')
        hashpass = encrypt_string(password)  # password doesn't need any sanitation since it is hashed
        # print(username, password, hashpass)

        if 'login' in request.form:  # if login was pressed
            # find all users with username
            # print("before execute")
            userswithname = db.execute("SELECT username,password FROM users WHERE username=:u AND password=:p",
                                       {"u": username, "p": hashpass}).fetchall()
            # print("after execute")
            # if username or password doesn't match
            if len(userswithname) == 0:
                return render_template('login.html', logError='Username or password is incorrect', user=session["user"])
            session["user"] = username
            print(f"User {username} has logged in")
            return redirect(url_for('search'))

        elif 'register' in request.form:  # if register was pressed
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

            # check if password matches confirmed password
            checkpassword = request.form.get('ConfirmPassword')
            if password != checkpassword:
                return render_template('login.html', regError='Passwords must match',
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


@app.route("/search", methods=["GET", "POST"])
def search():
    # redirect unlogged users to homepage
    if session.get("user") is None:
        return redirect(url_for('home'))
    elif session.get("user") == '':
        return redirect(url_for('home'))
    # get method
    if request.method == "GET":
        return render_template('search.html', user=session["user"])

    # post method, get all form values
    isbn = SQLquotes(request.form.get('isbn'))
    title = SQLquotes(request.form.get('title'))
    author = SQLquotes(request.form.get('author'))
    year = request.form.get('year')
    # print(f"{isbn}, {title}, {author}, {year}")

    # build SQL query
    command = ("SELECT * FROM books WHERE "
               "isbn LIKE '%%%(isbn)s%%' AND "
               "title LIKE '%%%(title)s%%' AND "
               "author LIKE '%%%(author)s%%'" % {
                   "isbn": isbn, 'title': title, "author": author})
    # 'year' cannot use LIKE operator, so only include if the user submitted it
    if year != '':
        command = command + " AND year = '%(year)s'" % {'year': year}
    # print(command)

    # query the database for books
    foundbooks = db.execute(command).fetchall()
    # print(foundbooks)

    return render_template('search.html', user=session["user"], numbooks=len(foundbooks), books=foundbooks)


@app.route("/book", methods=["GET", "POST"])
def book():
    # redirect unlogged users to homepage
    if session.get("user") is None:
        return redirect(url_for('home'))
    elif session.get("user") == '':
        return redirect(url_for('home'))

    # get request (coming from search page)
    if request.method == "GET":
        # get book variables from page url
        session['isbn'] = request.args.get('isbn', None)
        session['title'] = request.args.get('title', None)
        session['author'] = request.args.get('author', None)
        session['year'] = request.args.get('year', None)

        # if any of the above is none, give 404 page
        if session['isbn'] is None or session['title'] is None or session['author'] is None or session['year'] is None:
            abort(404)

        print(f"Request info on: {session['isbn']}, {session['title']}, {session['author']}, {session['year']}")
        return render_template('book.html', user=session["user"], isbn=session['isbn'], title=session['title'],
                               author=session['author'], year=session['year'])
    # post request (submitting a review)
    else:
        rating = request.form.get('rating')
        review = request.form.get('review')
        print(rating, review)
        if rating is None:
            return render_template('book.html', user=session["user"], isbn=session['isbn'], title=session['title'],
                                   author=session['author'], year=session['year'],
                                   SubmitError="Must rate at last one star")
        elif review == "":
            return render_template('book.html', user=session["user"], isbn=session['isbn'], title=session['title'],
                                   author=session['author'], year=session['year'],
                                   SubmitError="Must write a review")
        # valid review has been submitted, make sure that the book exists in database


        return render_template('book.html', user=session["user"], isbn=session['isbn'], title=session['title'],
                               author=session['author'], year=session['year'])


if __name__ == '__main__':
    app.run(host='0.0.0.0')
