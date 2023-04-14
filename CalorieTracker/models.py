import time
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

db = SQLAlchemy()

class User(db.Model):
	__tablename__ = 'user'
	user_id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(24), nullable=False)
	pw_hash = db.Column(db.String(64), nullable=False)
	age = db.Column(db.Integer, nullable=False)
	weight = db.Column(db.Integer, nullable=False)
	height = db.Column(db.Integer, nullable=False)
	chatrooms = relationship("Chatroom", backref="user", lazy="dynamic", foreign_keys='Chatroom.parent_id', post_update=True)
	messages = relationship("Message", backref="user", lazy="dynamic", foreign_keys='Message.messToUser_id', post_update=True)
	curr_room = db.Column(db.Integer, db.ForeignKey('chatroom.chatroom_id', use_alter=True), nullable=True)
	update = db.Column(db.DateTime, nullable=True)
	
	def __init__(self, username, pw_hash, update, age, weight, height):
		self.username = username
		self.pw_hash = pw_hash
		self.update = update
		self.age = age
		self.weight = weight
		self.height = height

	def __repr__(self):
		return '{}'.format(self.username)

class Chatroom(db.Model):
	__tablename__ = 'chatroom'
	chatroom_id = db.Column(db.Integer, primary_key=True)
	chatname = db.Column(db.String(24), nullable=False)
	parent_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=True)
	messages = relationship("Message", backref="chatroom", lazy="dynamic")
	users = relationship("User", backref="chatroom", lazy="dynamic", foreign_keys='User.curr_room', post_update=True)
	date_created = db.Column(db.DateTime, nullable=True)
	activity_type = db.Column(db.String(24), nullable=False)
	duration = db.Column(db.Integer, nullable=False)
	duration_minutes = db.Column(db.Integer, nullable=False)
	calculation = db.Column(db.Integer, nullable=False)
	weight = db.Column(db.Integer, nullable=False)
	height = db.Column(db.Integer, nullable=False)
	age = db.Column(db.Integer, nullable=False)
	

	def __init__(self, chatname, parent_id, date_created, activity_type, duration, duration_minutes, calculation, weight, height, age):
		self.chatname = chatname   
		self.parent_id = parent_id
		self.date_created = date_created
		self.activity_type = activity_type
		self.duration = duration
		self.duration_minutes = duration_minutes
		self.calculation = calculation
		self.weight = weight
		self.height = height
		self.age = age
	
class Message(db.Model):
	__tablename__ = 'message'
	message_id = db.Column(db.Integer, primary_key=True)
	meat = db.Column(db.String(64), nullable=False)
	messToChat_id = db.Column(db.Integer, db.ForeignKey('chatroom.chatroom_id'), nullable=True)
	messToUser_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=True)
	date = db.Column(db.DateTime, nullable=False)
	
	def __init__(self, meat, messToUser_id, date):
		self.meat = meat  
		self.messToUser_id = messToUser_id
		self.date = date
		#self.messToChat_id = messToChat_id
	