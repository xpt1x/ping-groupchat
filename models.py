from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    user_name = db.Column(db.String, primary_key = True, nullable=False)
    password = db.Column(db.String, nullable = False)
    admin = db.Column(db.Boolean, default=False)

    def __init__(self, user_name, password):
        self.user_name = user_name
        self.password = password

class Channel(db.Model):
    __tablename__ = 'channels'
    channelName = db.Column(db.String,primary_key=True, nullable=False)
    creator = db.Column(db.String, nullable=False)

    def __init__(self, channelName, creator):
        self.channelName = channelName
        self.creator = creator

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_name = db.Column(db.String, nullable = False)
    msg = db.Column(db.String, nullable = False)
    channelName = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable = False)

    def __init__(self, msg, user_name, channelName, time): 
        self.msg = msg
        self.user_name = user_name
        self.channelName = channelName
        self.time = time

class BannedUser(db.Model):
    __tablename__ = 'banned'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    channel = db.Column(db.String, nullable=False)
    user = db.Column(db.String, nullable=False)

    def __init__(self, channel, user):
        self.channel = channel
        self.user = user