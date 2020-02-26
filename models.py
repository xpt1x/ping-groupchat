from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    user_name = db.Column(db.String, primary_key = True, nullable=False)
    password = db.Column(db.String, nullable = False)

    def __init__(self, user_name, password):
        self.user_name = user_name
        self.password = password

class Channel(db.Model):
    __tablename__ = 'channels'
    channelName = db.Column(db.String, primary_key=True, nullable=False)

    def __init__(self, channelName):
        self.channelName = channelName

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_name = db.Column(db.String, nullable = False)
    msg = db.Column(db.String, nullable = False)
    channelName = db.Column(db.String, db.ForeignKey('channels.channelName'), nullable=False)

    def __init__(self, msg, user_name, channelName): 
        self.msg = msg
        self.user_name = user_name
        self.channelName = channelName