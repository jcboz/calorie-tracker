import time
import os
import json
from hashlib import md5
from datetime import datetime
from flask import Flask, request, session, url_for, redirect, render_template, abort, g, flash, jsonify, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from sqlalchemy import not_, and_, cast, func

from models import db, User, Activity

# create our little application :)
app = Flask(__name__)

# configuration
PER_PAGE = 30
DEBUG = True
SECRET_KEY = 'development key'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(app.root_path, 'calorie.db')

app.config.from_object(__name__)
app.config.from_envvar('CALORIEAPP_SETTINGS', silent=True)

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
	
def get_activity_id(activity):
	"""Convenience method to look up the id for a activity."""
	rv = Activity.query.filter_by(activity=activity).first()
	return rv.activity_id if rv else None
	
def get_calories_burnt(activity, hours, minutes):
	"""Function for calculating calories burnt"""
	# calories = (time(mins) * MET * body weight(kg)) / 200
	
	hours = float(hours)
	minutes = float(minutes)
	if(hours > 0):
		time = (hours * 60) + minutes #converting to minutes
	else:
		time = minutes #make sure calc does not mult by 0 if hours <= 0
	
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
	elif activity == "Cycling":
		mET = 8
	elif activity == "Swimming":
		mET = 9.5
	else:
		mET = 0
	
	calculation = ((3.5 * mET * weight) / 200) * time
	return int(calculation) #type casting back to int because it looks nicer

@app.route('/', methods=['GET', 'POST'])
def home():
    """Shows the home screen with activities"""
    if not g.user:
        return redirect('/login')
    g.user.activity = None
    db.session.commit()
    activities = Activity.query.all()  
    print(activities)
    return render_template('home.html', activities=activities)
    
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if not g.user:
        return redirect('/login')
    if request.method == 'POST':
        return redirect('/editprofile')
    db.session.commit()
    return render_template('profile.html')
    
@app.route('/editprofile', methods=['GET', 'POST'])
def editprofile():
    if not g.user:
        return redirect('/login')
    if request.method == 'POST':
        name = request.form['username']
        height = request.form['height']
        weight = request.form['weight']
        age = request.form['age']
        print(name,height,weight,age)
        id = get_user_id(g.user.username)
        user = User.query.get(id)
        print(user.weight)
        user.username = name
        user.height = height
        user.weight = weight
        print(user.weight)
        user.age = age
        flash('You have successfully updated profile info')
        db.session.commit()
        return redirect('/profile')
    db.session.commit()
    return render_template('editprofile.html')

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
			return redirect(url_for('newActivity'))
	return render_template('login.html', error=error)

    
@app.route('/register', methods=['GET', 'POST'])
def register():
	"""Register an account"""
	
	error = None
	if request.method == 'POST':
		user = request.form['username']
		pw = request.form['password']
		age = request.form['age']
		weight = request.form['weight']
		height = request.form['height']

		if not user:
			error = 'You have to enter a username'
		elif not pw:
			error = 'You have to enter a password'
		elif pw != request.form['password2']:
			error = 'The two passwords do not match'
		elif get_user_id(user) is not None:
			error = 'The username is already taken'
		elif not age or age.isdigit() == False:
			error = 'Enter a valid age'
		elif not weight or weight.isdigit() == False:
			error = 'Enter a valid weight'
		elif not height or height.isdigit() == False:
			error = 'Enter a valid height'
		else:
			db.session.add(User(user, generate_password_hash(pw), None, age, weight, height))
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
	
@app.route('/newActivity', methods=['GET', 'POST'])
def newActivity():
	error = None
	calculation = 0
	activity = None
	durationHour = 0
	durationMinute = 0

	if not g.user:
		return redirect(url_for('home'))
	if request.method == 'POST':
		act = request.form['activitytype']
		durHr = request.form['duration']
		durMin = request.form['duration_minutes']

		if not act:
			error = 'You have to enter a valid activity'
		elif not durHr and durHr == False:
			error = 'You have to enter a duration'
		elif not durHr.isdigit() or durMin.isdigit() == False:
			error = 'You must enter non-negative numbers only'
		else:
			calculation = get_calories_burnt(act, durHr, durMin)
			storeActivity = request.form['userinfo'] if ('userinfo' in request.form) else None
			print(storeActivity)
			activity = act
			durationHour = durHr
			durationMinute = durMin
			if storeActivity is not None:
				db.session.add(Activity(act, g.user.user_id, datetime.now(), act, durHr, durMin, calculation, g.user.weight, g.user.height, g.user.age))
				db.session.commit()
				flash('You have successfully saved a new activity')

	return render_template('newActivity.html', error=error, calculation=calculation, activity=activity, durationHour=durationHour, durationMinute=durationMinute)
	
@app.route('/delete/<activityid>')
def delete(activityid):
	if not g.user:
		return redirect('/login')
	if not activityid:
		abort(404)
	
	activity = Activity.query.filter_by(activity_id=activityid).first()
	db.session.delete(activity)
	db.session.commit()
	flash('Calculation successfully deleted')
	return redirect(url_for('home'))
	
@app.route('/activity/<activityid>', methods=['GET', 'POST'])
def activity(activityid):
	room = Activity.query.filter_by(activity_id=activityid).first()
	if room is None:
		abort(404)
	room.users.append(g.user)
	g.user.update = None
	db.session.commit()
	return render_template('activity.html', activity=room)
	
@app.route('/get_activities', methods=['GET'])
def get_activities():
	if not g.user:
		redirect(url_for('login'))
	if Activity.query.filter_by(activity_id=g.user.curr_room).first() is None:
		flash("Calculation has been deleted")
		abort(404)
	messyDict = []
	
	#get username, text, creation date
	#append dictionary containing string text gotten from user
	g.user.update = datetime.now()
	db.session.commit()
	return jsonify(messyDict)
	
@app.route('/get_profile', methods=['GET', 'POST'])
def get_profile():
	if not g.user:
		redirect(url_for('login'))
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
	
	if request.method == 'PATCH':
		name = request.form['name']
		height = request.form['height']
		weight = request.form['weight']
		age = request.form['age']
	
	id = get_user_id(g.user.username)
	user = User.query.get(id)
	user.username = name
	user.height = height
	user.weight = weight
	user.age = age
	
	db.session.commit()
	return jsonify(messyDict)
