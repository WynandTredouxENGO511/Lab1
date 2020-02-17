# ENGO551: Lab Assignment 1
Author: Wynand Tredoux

UCID: 30020515

# Objective
Build a webiste where users can register, login, saerch for books, leave reviews, and see reviews left by other users. They will also be able to see the ratings of these books from Goodreads.com's API, and will able to query this websites database for book ratings via this website's API.

# Files and Folders
	application.py - main application using flask to handle http requests to the site
	books.csv - csv file containing all the book imported into the site
	config.cfg - various options loaded by flask on startup
	import.py - python script that dynamically imports .csv files into postgres database tables
	requirements.txt - python packages needed for this project. Use `pip install -r requirements.txt` to install all packages
	runflask.bat - windows batch file defining necessary environment variables and starting the flask application
	runflask.sh - same as above, just for OSX/linux systems
	/templates - folder containing all the HTML templates for the website
		home.html - Home page containing a welcome message and the Geomatics/Schulich logos
		login.html - Page where users can login or register on the site
		search.html - Page where users can search for books
		book.html - Page that is dynamically created to show info from a book and leave ratings/reviews
		admin.hmtl - Admin page, only viewable by the 'admin' user, shows all current registered users
		api.html - Page containing info on how to use this site's API to query the database
		layout.html - Page containing the layout all other pages are based on
	/static - folder containing css files for the styling of the site
	/static/img - folder containing any images used on the site

# Video Demo
https://youtu.be/6uVgx1pPTBw