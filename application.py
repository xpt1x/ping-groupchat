import os, requests, socket

from flask import Flask, session, render_template, url_for, redirect, g, request, redirect, jsonify
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit, join_room, leave_room
from models import *
from sqlalchemy import and_

app = Flask(__name__)
socketio = SocketIO(app)

# 100 as prescribed in docs
msg_limit = 100
# Channels dictionary to store online users
Channels = dict()

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
                session.pop('user_name', None)
                return render_template('login.html', warnmsg='Please login again')
            # if user has no last channel
            if session.get('last_channel'):
                # send user to the last channel chat page
                return redirect('/channels/' + session.get('last_channel'))
            else:
                # show index page to create or join channel
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
                if session.get('last_channel'):
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
    # filled registeration form
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
        if session.get('user_name'):
            return redirect(url_for('index'))
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
        #update local dict and add this channel, create a empty obj
        Channels[request.form.get('channel')] = set()
        # set last channel for this user
        session['last_channel'] = request.form.get('channel')
        session['last_channel_creator'] = channel.creator
        # send user to chat page
        return render_template('chat.html', channel=channel, sucmsg='Channel created successfully')
    else:
        # user is redirected here
        return redirect(url_for('index'))

@app.route('/channels/<qchannel>')
def SetChannel(qchannel):
    if not session.get('user_name'):
        return redirect(url_for('index'))
    # check for last channel for this user
    same_channel = True

    if session.get('last_channel'):
        last_channel = Channel.query.get(session.get('last_channel'))
        # check if its valid or not
        if last_channel:
            # channel exists
            ichannel = last_channel
        else:
            same_channel = False

    if not same_channel or not session.get('last_channel'):
        ichannel = Channel.query.get(qchannel)

    if not ichannel:
        return render_template('index.html', channels=Channel.query.all(), errmsg='Channel not found!')
    #check if user is allowed or not
    if not IsAllowed(session.get('user_name'), ichannel):
        return render_template('index.html', channels=Channel.query.all(), errmsg='Sorry! You are banned from this channel')
    # fetch old messages ( limit by msg_limit )
    msgs = Message.query.filter_by(channelName=ichannel.channelName).order_by(Message.id).all()
    msgs = msgs[-msg_limit:]
    
    session['last_channel'] = ichannel.channelName
    session['last_channel_creator'] = ichannel.creator
    return render_template('chat.html', channel=ichannel, msgs=msgs)

@socketio.on('user joined')
def room_joined():
    room = session.get('last_channel')
    join_room(room)
    if room not in Channels:
        Channels[room] = set()
    Channels[room].add(session.get('user_name'))
    emit('on user join', {
        'user_name': session.get('user_name'),
        'channel': session.get('last_channel'),
        'users': list(Channels[room])
    }, room=room, broadcast=True)

@socketio.on('user left')
def room_left():
    room = session.get('last_channel')
    leave_room(room)
    Channels[room].discard(session.get('user_name'))
    li = set()
    session.pop('last_channel', None)
    session.pop('last_channel_creator', None)
    emit('left announce', {
        'user_name': session.get('user_name'),
        'users': list(Channels[room])
    }, room=room)

@socketio.on('channel destroy clicked')
def destroy_channel():
    room = session.get('last_channel')
    leave_room(room)
    # deleting from local dict Channels
    if room in Channels:
        Channels.pop(session.get('last_channel'), None)
    # deleting all messages associated with channel
    all_msgs = Message.__table__.delete().where(Message.channelName == room)
    db.session.execute(all_msgs)
    db.session.commit()
    # delete channel from db
    db.session.delete(Channel.query.get(room))
    db.session.commit()

    session.pop('last_channel', None)
    session.pop('last_channel_creator', None)
    emit('destroy announce', room=room, broadcast=True)

@socketio.on('chat prune clicked')
def PruneChat():
    room = session.get('last_channel')
    # deleting all messages associated with channel
    all_msgs = Message.__table__.delete().where(Message.channelName == room)
    db.session.execute(all_msgs)
    db.session.commit()

    emit('prune announce', {'user_name': session.get('user_name')}, room=room)   

@socketio.on('ban clicked')
def BanUser(data):
    # not self
    if data['user'] != session.get('user_name'):
        usr = BannedUser(session.get('last_channel'), data['user'])
        db.session.add(usr)
        db.session.commit()
        emit('user banned', {'user': data['user'], 'by': session.get('user_name')}, room=session.get('last_channel'))

@socketio.on('unban clicked')
def UnBanUser(data):
    BannedUser.query.filter(and_(BannedUser.user == data['user'], BannedUser.channel == session.get('last_channel'))).delete()
    db.session.commit()
    emit('user unbanned', {'user': data['user'], 'by': session.get('user_name')}, room=session.get('last_channel'))

@socketio.on('send message')
def AnnounceMsg(data):
    # add data to DB
    msg = Message(msg=data['msg'], user_name=session.get('user_name') , channelName=session.get('last_channel'), time=data['time'])
    
    db.session.add(msg)
    db.session.commit()
    data['by'] = session.get('user_name')
    form_msg = ''

    if session.get('last_channel_creator') == data['by']:
        form_msg = f"<strong style='color: #0388fc;'>{data['by']}</strong>: {data['msg']}"
    else:
        form_msg = f"<strong>{data['by']}</strong>: {data['msg']}"

    data['form_msg'] = form_msg
    room = session.get('last_channel')
    emit('recieved message', data, room=room, broadcast=True)

@socketio.on('user typing')
def AnnounceTyping():
    emit('user is typing', {'user': session.get('user_name')}, room=session.get('last_channel'), broadcast=True)

@socketio.on('typing cleared')
def ClearTypingBox():
    emit('clear typing box', room=session.get('last_channel'), broadcast=True)

@app.route('/logout')
def log_out():
    session.pop('last_channel', None)
    session.pop('user_name', None)
    session.pop('last_channel_creator', None)

    return redirect(url_for('index'))

@app.route('/leave')
def LeaveRoute():
    Channels[session.get('last_channel')].discard(session.get('user_name'))
    session.pop('last_channel', None)
    session.pop('last_channel_creator', None)
    return redirect(url_for('index'))

@app.route('/chnlDstryd')
def ChannelDestroyed():
    session.pop('last_channel', None)
    session.pop('last_channel_creator', None)
    return redirect(url_for('index'))

@app.route('/user', methods=['POST'])
def UserPanel():
    channels = Channel.query.all()
    if not request.form.get('newpass'):
        return render_template('index.html', channels=channels, errmsg='Must provide new password')
    if not request.form.get('confirmpass'):
        return render_template('index.html', channels=channels, errmsg='Must provide confirmation of new password')
    if request.form.get('newpass') != request.form.get('confirmpass'):  
        return render_template('index.html', channels=channels, errmsg='Passwords doesnt match, retry')
    
    user = User.query.get(session.get('user_name'))
    user.password = generate_password_hash(request.form.get('newpass'), method='pbkdf2:sha256', salt_length=8)
    db.session.commit()
    return render_template('index.html', channels=channels, sucmsg='Password updated Successfully')

####### API ROUTES to collect useful Info 
@app.route('/userinfo/<channel>')
def SendUsersInfo(channel):
    'API route to request users info'
    if channel in Channels.keys():
        if len(Channels[channel]) == 0:
            return jsonify({'status': 404})
        else:
            return jsonify({'status': 200, 'users':list(Channels[channel])})
    #else return 404
    else:
        return jsonify({'status': 404})

@app.route('/bannedUsers/<ichannel>')
def BannedUsersInfo(ichannel):
    'API route to request banned users info'
    UserList = BannedUser.query.filter_by(channel=ichannel).all()
    if not UserList:
        return jsonify({'status': 404})
    
    li = list()
    for iuser in UserList:
        li.append(iuser.user)
    return jsonify({'status': 200, 'users': li})

@app.route('/user')
def SendUserName():
    if session.get('user_name'):
        return jsonify({'status': 200, 'name': session.get('user_name')})
    else:
        return jsonify({'status': 404})
# ####### END API Routes

def IsAllowed(username, ichannel):
    if not BannedUser.query.filter(and_(BannedUser.user == username, BannedUser.channel == ichannel.channelName)).first():
        return True
    return False

@app.before_request
def BeforeRequest():
    session.permanent = True
    if not request.is_secure and app.env != "DEVELOPMENT":
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)

if __name__ == '__main__':
    socketio.run(app, debug=True)