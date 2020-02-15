"""
Environemnt variables:
FLASK_APP=application.py
DATABASE_URL=postgres://qbtxfingwrqmyc:962e9c32a97ff8eb6dff5e85a07032b9a9758d9da76c231864487642df21726a@ec2-35-168-54-239.compute-1.amazonaws.com:5432/d3tu5tucael6mf
API_KEY=v6TC76FrNDwCdsxMwPBNg
"""

import os
import hashlib
import requests

from flask import Flask, session, request, render_template, redirect, url_for, abort, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


# function used to hash user passwords
def encrypt_string(hash_string):
    sha_signature = \
        hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature


# mean fucntion
def mean(list):
    if len(list) == 0:
        return 0
    sums = 0.0
    for i in list:
        sums += i
    return sums / len(list)


# function to deal with quotes in SQL queries
def SQLquotes(str):
    if "'" in str:
        return str.replace("'", "''")
    else:
        return str


# function to separate review list into score, user, and review text
def parsReviews(reviews):
    review_scores = []
    review_text = []
    review_users = []
    for r in reviews:
        review_scores.append(r[3])
        review_text.append(r[2])
        review_users.append(r[0])
    return review_scores, review_text, review_users


app = Flask(__name__)

# Check for DATABASE_URL variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")
# Check for API_KEY variable
if not os.getenv("API_KEY"):
    raise RuntimeError("API_KEY is not set")
KEY = os.getenv("API_KEY")

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

        if 'login' in request.form:  # if login was pressed
            # find all users with username
            userswithname = db.execute("SELECT username,password FROM users WHERE username=:u AND password=:p",
                                       {"u": username, "p": hashpass}).fetchall()
            # if username or password doesn't match
            if len(userswithname) == 0:
                return render_template('login.html', logError='Username or password is incorrect', user=session["user"])
            session["user"] = username
            print(f"User {username} has logged in")
            return redirect(url_for('search'))

        elif 'register' in request.form:  # if register was pressed
            print('register')
            # HTML form checks for blank fields already, but just to be safe
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
    session.clear()  # clear session for user on logout
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

    # build SQL query
    command = ("SELECT * FROM books WHERE "
               "isbn LIKE '%%%(isbn)s%%' AND "
               "title LIKE '%%%(title)s%%' AND "
               "author LIKE '%%%(author)s%%'" % {
                   "isbn": isbn, 'title': title, "author": author})
    # 'year' cannot use LIKE operator, so only include if the user submitted it
    if year != '':
        command = command + " AND year = '%(year)s'" % {'year': year}
    # add ORDER BY title
    command += " ORDER BY title ASC"

    # query the database for books
    foundbooks = db.execute(command).fetchall()

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
        session['isbn'] = request.args.get('isbn')
        session['title'] = request.args.get('title')
        session['author'] = request.args.get('author')
        session['year'] = request.args.get('year')

        # if any of the above is none, give 404 page
        if session['isbn'] is None or session['title'] is None or session['author'] is None or session['year'] is None:
            abort(404)

        print(f"Request info on: {session['isbn']}, {session['title']}, {session['author']}, {session['year']}")
        # build sql command to select book
        command = ("SELECT * FROM books WHERE "
                   "isbn='%(isbn)s' AND "
                   "title='%(title)s' AND "
                   "author='%(author)s' AND "
                   "year='%(year)s'" % {
                       "isbn": session['isbn'], 'title': session['title'], "author": session['author'],
                       "year": session['year']})
        # check that book with above info exists in database
        if len(db.execute(command).fetchall()) == 0:
            # if book does not exist
            return render_template('book.html', user=session["user"], isbn=session['isbn'], title=session['title'],
                                   author=session['author'], year=session['year'],
                                   DBError="Book not found")
        # get reviews from database
        command = ("SELECT * FROM reviews WHERE isbn='%(isbn)s'" % {"isbn": session['isbn']})
        reviews = db.execute(command).fetchall()
        # separate review list into score, user, and review text
        session['review_scores'], session['review_text'], session['review_users'] = parsReviews(reviews)

        # define session variables to save Goodreads info
        session['Gnumrating'] = 0
        session['Gavgrating'] = 0
        # get ratings from Goodreads
        res = requests.get("https://www.goodreads.com/book/review_counts.json",
                           params={"key": KEY, "isbns": session['isbn']})
        if res.status_code != 200:
            print('Error: Goodreads could not find book')
        else:
            data = res.json()
            session['Gnumrating'] = data['books'][0]['work_ratings_count']
            session['Gavgrating'] = data['books'][0]['average_rating']

        return render_template('book.html', user=session["user"], isbn=session['isbn'], title=session['title'],
                               author=session['author'], year=session['year'], scores=session['review_scores'],
                               text=session['review_text'], users=session['review_users'],
                               avgscore=mean(session['review_scores']),
                               numreviews=len(session['review_scores']), Gnum=session['Gnumrating'],
                               Gavg=session['Gavgrating'])

    # post request (submitting a review)
    else:
        rating = request.form.get('rating')
        review_us = request.form.get('review')
        review = SQLquotes(review_us)  # escape quotes from text input
        print(rating, review)
        if rating is None:
            return render_template('book.html', user=session["user"], isbn=session['isbn'], title=session['title'],
                                   author=session['author'], year=session['year'], scores=session['review_scores'],
                                   text=session['review_text'], users=session['review_users'],
                                   avgscore=mean(session['review_scores']),
                                   numreviews=len(session['review_scores']), Gnum=session['Gnumrating'],
                                   Gavg=session['Gavgrating'],
                                   SubmitError="Must rate at last one star")
        elif review == "":
            return render_template('book.html', user=session["user"], isbn=session['isbn'], title=session['title'],
                                   author=session['author'], year=session['year'], scores=session['review_scores'],
                                   text=session['review_text'], users=session['review_users'],
                                   avgscore=mean(session['review_scores']),
                                   numreviews=len(session['review_scores']), Gnum=session['Gnumrating'],
                                   Gavg=session['Gavgrating'],
                                   SubmitError="Must write a review")

        # valid review has been submitted, GET method already checked that the book exists
        # check that user has not already submitted a review for this book
        if len(db.execute("SELECT username FROM reviews WHERE username='%(username)s' AND isbn='%(isbn)s'" % {
            'username': session["user"], 'isbn': session['isbn']}).fetchall()) != 0:
            return render_template('book.html', user=session["user"], isbn=session['isbn'], title=session['title'],
                                   author=session['author'], year=session['year'], scores=session['review_scores'],
                                   text=session['review_text'], users=session['review_users'],
                                   avgscore=mean(session['review_scores']),
                                   numreviews=len(session['review_scores']), Gnum=session['Gnumrating'],
                                   Gavg=session['Gavgrating'],
                                   SubmitError="You cannot submit another review for this book")
        # submit review to database
        db.execute("INSERT INTO reviews (username, isbn, review, rating) "
                   "VALUES ('%(user)s', '%(isbn)s', '%(review_text)s', '%(review_rating)s')"
                   % {'user': session["user"], 'isbn': session['isbn'], 'review_text': review, 'review_rating': rating})
        db.commit()
        print("review submitted!")
        # add review to session variables so the page info updates immediately
        session['review_scores'].append(int(rating))
        session['review_users'].append(session['user'])
        session['review_text'].append(review_us)

        return render_template('book.html', user=session["user"], isbn=session['isbn'], title=session['title'],
                               author=session['author'], year=session['year'], scores=session['review_scores'],
                               text=session['review_text'], users=session['review_users'],
                               avgscore=mean(session['review_scores']),
                               numreviews=len(session['review_scores']), Gnum=session['Gnumrating'],
                               Gavg=session['Gavgrating'], Rsubmit=1)


# API access
@app.route("/api/<isbn>")
def api(isbn):
    # query database for book with given isbn
    command = ("SELECT * FROM books WHERE isbn='%(isbn)s'" % {"isbn": isbn})
    book = db.execute(command).fetchall()

    # if no book found
    if len(book) == 0:
        abort(404)
    # if book found, get review scores
    command = ("SELECT * FROM reviews WHERE isbn='%(isbn)s'" % {"isbn": isbn})
    reviews = db.execute(command).fetchall()
    review_scores = parsReviews(reviews)[0]
    # calculate number of reviews and average score
    numrating = len(review_scores)
    avgrating = mean(review_scores)

    # build json
    title = book[0][1]
    author = book[0][2]
    year = book[0][3]
    return jsonify(title=title,
                   author=author,
                   isbn=isbn,
                   year=year,
                   review_count=numrating,
                   average_score=avgrating)


# API access info page
@app.route("/api_info")
def api_info():
    if session.get("user") is None:  # initialize user to empty
        session["user"] = ''

    return render_template('api.html', user=session["user"])


if __name__ == '__main__':
    app.run(host='0.0.0.0')
