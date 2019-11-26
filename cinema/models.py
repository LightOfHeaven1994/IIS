from cinema import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


class User(db.Model, UserMixin):

	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(20), unique=True, nullable=False)
	email = db.Column(db.String(60), unique=True, nullable=False)
	password = db.Column(db.String(60), nullable=False)
	profile_picture = db.Column(db.String(20), nullable=False, default='default.jpg')
	role = db.Column(db.String(20), nullable=False, default='User')
	reservations = db.relationship('Reservation')

	def __repr__(self):
		return f"User('{self.username}', '{self.email}', {self.role})"


class Reservation(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	tickets = db.relationship('Ticket')


class Ticket(db.Model):

	id = db.Column(db.Integer, primary_key=True)
	price = db.Column(db.Integer, nullable=False)
	reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.id'), nullable=False)
	seats = db.relationship('Seat')


event_hall = db.Table('event_hall', db.Column('event_id', db.Integer, db.ForeignKey('event.id')),
	db.Column('date_id', db.Integer, db.ForeignKey('date.id')), 
	db.Column('hall_id', db.Integer, db.ForeignKey('hall.id')))


class Event(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(60), unique=True, nullable=False)
	picture = db.Column(db.String(20), nullable=False, default='default_event.jpg')
	event_type = db.Column(db.String(60), nullable=False)
	duration = db.Column(db.Integer, nullable=False)
	language = db.Column(db.String(10), nullable=False)
	age_restriction = db.Column(db.Integer(), nullable=False)


	def __repr__(self):
		return f"Event('{self.name}, {self.event_type}, {self.duration}, {self.language}, {self.age_restriction}')"


# hall_date = db.Table('hall_date', db.Column('hall_id', db.Integer, db.ForeignKey('hall.id')),
# 	db.Column('date_id', db.Integer, db.ForeignKey('date.id')))


class Date(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.String(13), nullable=False)
	alldates = db.relationship('Event', secondary=event_hall,
							backref=db.backref('dates_of_event',lazy='dynamic'))
	alldates_in_hall = db.relationship('Hall', secondary=event_hall,
							backref=db.backref('dates_for_hall', lazy='dynamic'))

  
class Hall(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	hall_name = db.Column(db.String(30), nullable=False)
	seats = db.relationship('Seat')
	events_in_hall = db.relationship('Event', secondary=event_hall,
							backref=db.backref('halls_of_event', lazy='dynamic'))


	def __repr__(self):
		return f"Hall('{self.hall_name}')"


class Seat(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	row = db.Column(db.Integer, nullable=False)
	number = db.Column(db.Integer, nullable=False)
	is_busy = db.Column(db.Boolean, default=False)
	hall_id = db.Column(db.Integer, db.ForeignKey('hall.id'), nullable=False)
	ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'))

	def __repr__(self):
		return f"Seat('{self.row}', '{self.number}')"
