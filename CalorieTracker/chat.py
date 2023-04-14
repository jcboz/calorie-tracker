import time
import os
import json
from hashlib import md5
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash, _app_ctx_stack, jsonify, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from sqlalchemy import not_, and_, cast, func

from models import db, User, Chatroom, Message

# create our little application :)
app = Flask(__name__)

# configuration
PER_PAGE = 30
DEBUG = True
SECRET_KEY = 'development key'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.root_path, 'chat.db')

app.config.from_object(__name__)
app.config.from_envvar('CHATAPP_SETTINGS', silent=True)

db.init_app(app)


@app.cli.command('initdb')
def initdb_command():
	"""Creates the database tables."""
	db.create_all()
	db.session.commit()
	print('Initialized the database.')

@app.cli.command('deletedb')
def deletedb_command():
	db.drop_all()
	
@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.filter_by(user_id=session['user_id']).first()

def get_user_id(username):
	"""Convenience method to look up the id for a username."""
	rv = User.query.filter_by(username=username).first()
	return rv.user_id if rv else None
	
def get_chatroom_id(chatname):
	"""Convenience method to look up the id for a chatroom."""
	rv = Chatroom.query.filter_by(chatname=chatname).first()
	return rv.chatroom_id if rv else None
	
def get_message_id(meat):
	"""Convenience method to look up the id for a message"""
	rv = Message.query.filter_by(meat=meat).first()
	return rv.chatroom_id if rv else None
	
def get_calories_burnt(activity, hours, minutes):
	"""Function for calculating calories burnt"""
	# calories = (time(mins) * MET * body weight(kg)) / 200
	time = (float(hours) * 60) + float(minutes) #converting to minutes
	print(time, "this is a test")
	weight = g.user.weight / 2.205 #converting to kg
	# Every exercise has an MET index that basically says how hard it is and is used to calculate how many calories are burnt
	# They vary though so the ones I used come from the websites: 
	# https://community.plu.edu/~chasega/met.html
	# https://www.healthline.com/health/what-are-mets#examples
	# And the formula I used below comes from the website:
	# https://www.calculator.net/calories-burned-calculator.html?activity=1&activity2=Running%3A+moderate&chour=1&cmin=&cweight=160&cweightunit=p&ctype=1&x=99&y=19
	# also all of these activities would be under "moderate" so like an average runner but we could get more specific if we have time
	if activity == "Running":
		mET = 11.5
	elif activity == "Walking":
		mET = 5
	elif activity == "Cylcing":
		mET = 8
	elif activity == "Swimming":
		mET = 9.5
	else:
		mET = 0
	
	calculation = ((3.5 * mET * weight) / 200) * time
	return int(calculation) #type casting back to int because it looks nicer

@app.route('/', methods=['GET', 'POST'])
def home():
    """Shows the home screen with available chat rooms"""
    if not g.user:
        return redirect('/login')
    g.user.chatroom = None
    db.session.commit()
    chatrooms = Chatroom.query.all()  
    print(chatrooms)
    return render_template('home.html', chatrooms=chatrooms)
    
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not g.user:
        return redirect('/login')
    db.session.commit()
    return render_template('profile.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	if request.method == 'POST':

		user = User.query.filter_by(username=request.form['username']).first()
		if user is None:
			error = 'Invalid username or password'
		elif not check_password_hash(user.pw_hash, request.form['password']):
			error = 'Invalid username or password'
		else:
			flash('You were logged in')
			session['user_id'] = user.user_id
			return redirect(url_for('createChat'))
	return render_template('login.html', error=error)

    
@app.route('/register', methods=['GET', 'POST'])
def register():
	"""Register an account"""
	error = None
	if request.method == 'POST':
		if not request.form['username']:
			error = 'You have to enter a username'
		elif not request.form['password']:
			error = 'You have to enter a password'
		elif request.form['password'] != request.form['password2']:
			error = 'The two passwords do not match'
		elif get_user_id(request.form['username']) is not None:
			error = 'The username is already taken'
		else:
			db.session.add(User(request.form['username'], generate_password_hash(request.form['password']), None, request.form['age'], request.form['weight'], request.form['height']))
			db.session.commit()
			flash('You were successfully registered and can login now')
			return redirect(url_for('login'))
	return render_template('register.html', error=error)
	
@app.route('/logout')
def logout():
	"""Logs the user out."""
	flash('You were logged out')
	session.pop('user_id', None)
	return redirect(url_for('home'))
	
@app.route('/createChat', methods=['GET', 'POST'])
def createChat():
	error = None
	if not g.user:
		return redirect(url_for('home'))
	if request.method == 'POST':
		if not request.form['activitytype']:
			error = 'You have to enter an activity'
		elif not request.form['duration']:
			error = 'You have to enter duration'
		elif not request.form['duration_minutes']:
			error = 'You have to enter duration minutes'
		else:
			db.session.add(Chatroom(request.form['activitytype'], g.user.user_id, datetime.now(), request.form['activitytype'], request.form['duration'], request.form['duration_minutes'], get_calories_burnt(request.form['activitytype'], request.form['duration'], request.form['duration_minutes'])))
			db.session.commit()
			flash('You have successfully calculated a new activity')
	return render_template('createChat.html', error=error)
	
@app.route('/delete/<chatroomid>')
def delete(chatroomid):
	if not g.user:
		return redirect('/login')
	if not chatroomid:
		abort(404)
	
	chatroom = Chatroom.query.filter_by(chatroom_id=chatroomid).first()
	db.session.delete(chatroom)
	db.session.commit()
	flash('Chat Room successfully deleted')
	return redirect(url_for('home'))
	
# @app.route('/join/<chatroomid>')
# def join(chatroomid):
# 	if not g.user:
# 		return redirect('/login')
# 	if not chatroomid:
# 		abort(404)
# 	room = Chatroom.query.filter_by(chatroom_id=chatroomid).first()
# 	users = room.users
# 	users.append(g.user)
# 	room.users = users
# 	db.session.commit()
# 	flash('Chat successfully joined')
# 	return redirect(url_for('new_chatroom'))
	
	
@app.route('/chatroom/<chatroomid>', methods=['GET', 'POST'])
def chatroom(chatroomid):
	room = Chatroom.query.filter_by(chatroom_id=chatroomid).first()
	if room is None:
		abort(404)
	room.users.append(g.user)
	g.user.update = None
	db.session.commit()
	return render_template('chatroom.html', chatroom=room)
	
@app.route('/chatroom/create-post', methods=['POST'])
def create_post():
	req = request.get_json()
	res = make_response(jsonify(req), 200)
	if not request.json['meat']:
		error = 'You have to enter a message'
	else:
		message = Message(request.json['meat'], g.user.user_id, datetime.now())
		db.session.add(message)
		g.user.chatroom.messages.append(message)
		db.session.commit()
		flash('You have successfully posted')
	return res
	
@app.route('/get_messages', methods=['GET'])
def get_messages():
	if not g.user:
		redirect(url_for('login'))
	if Chatroom.query.filter_by(chatroom_id=g.user.curr_room).first() is None:
		flash("Room has been deleted")
		abort(404)
	if g.user.update is None:
		msgs = Message.query.filter_by(chatroom=g.user.chatroom).order_by(Message.date).all()
	else:
		msgs = Message.query.filter_by(chatroom=g.user.chatroom).filter(Message.date > g.user.update).order_by(Message.date).all()
	print(msgs)
	messyDict = []
	#create an empty array, iterate over all messages queried. 
	for msg in msgs:
		dictionary = {
		'user': msg.user.username,
		'content': msg.meat,
		'date': str(msg.date),
		}
		messyDict.append(dictionary)
	#get username, text, creation date
	#append dictionary containing string text gotten from user
	g.user.update = datetime.now()
	db.session.commit()
	return jsonify(messyDict)
	
@app.route('/get_profile', methods=['GET'])
def get_profile():
	if not g.user:
		redirect(url_for('login'))
	#if Chatroom.query.filter_by(chatroom_id=g.user.curr_room).first() is None:
	#	flash("Room has been deleted")
	#	abort(404)
	# print(g.user.username + "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
	messyDict = []
	#create an empty array, iterate over all messages queried. 
	dictionary = {
		'user': g.user.username,
		'age': g.user.age,
		'weight':g.user.weight,
		'height':g.user.height
		}
	messyDict.append(dictionary)
	#get username, text, creation date
	#append dictionary containing string text gotten from user
	db.session.commit()
	return jsonify(messyDict)
