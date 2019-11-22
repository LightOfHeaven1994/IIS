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

	def __repr__(self):
		return f"User('{self.username}', '{self.email}')"


class Event(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(60), unique=True, nullable=False)
	picture = db.Column(db.String(20), nullable=False, default='default_event.jpg')
	event_type = db.Column(db.String(60), nullable=False)
	duration = db.Column(db.Integer, nullable=False)
	pruduction = db.Column(db.String(60))
	language = db.Column(db.String(10), nullable=False)
	age_restriction = db.Column(db.Integer(), nullable=False)

	def __repr__(self):
		return f"Event('{self.name}, {self.event_type}, {self.duration}, {self.pruduction}, {self.language}, {self.age_restriction}')"
