# PING - Minimalist GroupChat
Web application which provides real time communication with help of Socket.IO, options like channel creation/join, user registration/login, basic channel features are there. All features of the application are listed on registration page under a button **Display app features**

## TEST RUN
https://ping-xpt1x.herokuapp.com/
`Powered by heroku`
## Installation
In order to run this project, you must have python3 installed on your system
```bash
#environment vars
$ export FLASK_APP = application.py
$ export DATABASE_URL=''
$ export SECRET_KEY = ''

# clone this repo with git
$ git clone https://github.com/xpt1x/ping-groupchat.git
$ cd ping-groupchat
$ pip install -r requirements.txt

# now create tables in db
$ python create.py

# finally run the application
$ flask run
```
```
SECRET_KEY can be set to any random string, this serves as a unique identifier for app
DATABASE_URL is a connection string with details from your db
```
## USAGE
- Create account or login
- Join a channel or create one
- Use channel to communicate with others
- Use channel features
