from cinema import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


class User(db.Model, UserMixin):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), unique=True, nullable=False)
	email = db.Column(db.String(60), unique=True, nullable=False)
	password = db.Column(db.String(60), nullable=False)
	profile_picture = db.Column(db.String(20), nullable=False, default='default.jpg')
	role = db.Column(db.String(20), nullable=False, default='User')
	#reservations = db.relationship('Reservation')

	def __repr__(self):
		return f"User('{self.username}', '{self.email}', {self.role})"

Event_data = db.Table('Hall_Event', db.Column('id', db.Integer, db.ForeignKey('events.id')),
	 db.Column('id', db.Integer, db.ForeignKey('dates.id')))

class Event(db.Model):
	__tablename__ = 'events'
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(60), unique=True, nullable=False)
	picture = db.Column(db.String(20), nullable=False, default='default_event.jpg')
	event_type = db.Column(db.String(60), nullable=False)
	duration = db.Column(db.Integer, nullable=False)
	language = db.Column(db.String(10), nullable=False)
	age_restriction = db.Column(db.Integer(), nullable=False)
	alldates = db.relationship('Date', secondary=Event_data,
							 backref=db.backref('dates'))

	def __repr__(self):
		return f"Event('{self.name}, {self.event_type}, {self.duration}, {self.language}, {self.age_restriction}')"




class Date(db.Model):
	__tablename__ = 'dates'
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.String(13), nullable=False)
