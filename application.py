import os, requests, socket

from flask import Flask, session, render_template, url_for, redirect, g, request, redirect
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit, join_room, leave_room
from models import *

app = Flask(__name__)
socketio = SocketIO(app)

# 100 as prescribed in docs
msg_limit = 100

# Check for environment variable, API KEY, SECRET KEY
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

if not os.getenv("SECRET_KEY"):
    raise RuntimeError("SECRET_KEY is not set")

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

# Configure session to use filesystem
app.config["SESSION_TYPE"] = "filesystem"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        if session.get('user_name'):
            # additional check for user details
            if not User.query.get(session.get('user_name')):
                session.pop('user_name')
                return render_template('login.html', warnmsg='Please login again')
            # if user has no last channel
            if session.get('last_channel'):
                # send user to the last channel chat page
                return redirect('/channels/' + session.get('last_channel'))
            else:
                channels = Channel.query.all()
                return render_template('index.html', channels=channels)
        else:
            return render_template('login.html')
    else:
        # user has filled login form, now query for this user

        if not request.form.get('username'):
            return render_template('login.html', errmsg='Must provide a username')
        if not request.form.get('password'):
            return render_template('login.html', errmsg='Must provide a password')

        # check DB for user and pass
        user = User.query.get(request.form.get('username'))
        if not user:
            return render_template('register.html', warnmsg='User not found! Please register first')
        else:
            # user found, check password 
            if check_password_hash(user.password, request.form.get('password')):
                session['user_name'] = user.user_name
                # send to last channel chat page
                if 'last_channel' in session:
                    return redirect('/channels/' + session.get('last_channel'))
                else:
                # no last channel, so display all channels + create page
                    channels = Channel.query.all()
                    return render_template('index.html', channels=channels, sucmsg='Login successful')
            # display error alert
            else:
                return render_template('login.html', errmsg='Wrong password! Please try again')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # validate fields
        if not request.form.get('username'):
            return render_template('register.html', errmsg='Must provide a username')
        if not request.form.get('password'):
            return render_template('register.html', errmsg='Must provide a password')
        # check if already exists
        if User.query.get(request.form.get('username')):
            return render_template('register.html', errmsg='User already exists! Try a different username for registeration')
        # all fine, create new user in DB 
        new_user = User(request.form.get('username'), generate_password_hash(request.form.get('password'), method='pbkdf2:sha256', salt_length=8))
        db.session.add(new_user)
        db.session.commit()
        # set local session username and send to home
        session['user_name'] = request.form.get('username')
        channels = Channel.query.all()
        return render_template('index.html', channels=channels, sucmsg='Registered successfully')
    else:
        # user is redirected here
        return render_template('register.html')

@app.route('/channel', methods=['GET', 'POST'])
def channel():
    channels = Channel.query.all()
    if request.method == 'POST':
        # submiited form for new channel
        # validate form
        if not request.form.get('channel'):
            return render_template('index.html', channels=channels, errmsg='Please provide a valid channel name')
        # check for existing channel
        if Channel.query.get(request.form.get('channel')):
            return render_template('index.html',channels=channels, errmsg='Channel already exists! Join it from list above')
        # channel doesnt exists and form is correct, add channel to db
        channel = Channel(request.form.get('channel'), session.get('user_name'))
        db.session.add(channel)
        db.session.commit()
        # set last channel for this user
        session['last_channel'] = request.form.get('channel')
        # send user to chat page
        channels = Channel.query.all()
        return render_template('chat.html', channel=channel, channels=channels, sucmsg='Channel created successfully')
    else:
        # user is redirected here
        return redirect(url_for('index'))

@app.route('/channels/<channel>')
def SetChannel(channel):
    # update user's last channel
    if not session.get('user_name'):
        return redirect(url_for('index'))
    session['last_channel'] = channel
    # fetch info for channel and other channels
    channels = Channel.query.all()
    # validate the channel first
    ichannel = Channel.query.get(channel)
    
    if not ichannel:
        return render_template('index.html', channels=channels, errmsg='Channel not found!')
    # fetch old messages ( limit by msg_limit )
    msgs = Message.query.filter_by(channelName=channel).all()
    msgs = msgs[-msg_limit:]
    # clicked any link and brought here
    return render_template('chat.html', channel=ichannel, channels=channels, msgs=msgs)

@socketio.on('user joined')
def room_joined():
    room = session.get('last_channel')
    join_room(room)
    emit('on user join', {
        'user_name': session.get('user_name'),
        'channel': session.get('last_channel')
    }, room=room, broadcast=True)

@socketio.on('channel destroy clicked')
def destroy_channel():
    room = session.get('last_channel')
    leave_room(room)
    # deleting all messages associated with channel
    all_msgs = Message.__table__.delete().where(Message.channelName == room)
    db.session.execute(all_msgs)
    db.session.commit()
    # delete channel from db
    db.session.delete(Channel.query.get(room))
    db.session.commit()

    session.pop('last_channel', None)
    emit('destroy announce', room=room)

@socketio.on('user left')
def room_left():
    room = session.get('last_channel')
    leave_room(room)
    session.pop('last_channel', None)
    emit('left announce', {
        'user_name': session.get('user_name'),
    }, room=room)

@socketio.on('send message')
def AnnounceMsg(data):
    # add data to DB
    msg = Message(msg=data['msg'], user_name=session.get('user_name') , channelName=session.get('last_channel'), time=data['time'])
    data['by'] = session.get('user_name')
    db.session.add(msg)
    db.session.commit()

    room = session.get('last_channel')
    emit('recieved message', data, room=room, broadcast=True)

@app.route('/logout')
def log_out():

    if session.get('last_channel'):
        session.pop('last_channel')
    if session.get('user_name'):
        session.pop('user_name')
    return redirect(url_for('index'))

@app.route('/leave')
def LeaveRoute():
    if session.get('last_channel'):
        session.pop('last_channel', None)

    return redirect(url_for('index'))

@app.before_request
def make_session_permanent():
    session.permanent = True

if __name__ == '__main__':
    socketio.run(app, debug=True)