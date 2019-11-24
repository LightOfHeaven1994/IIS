from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange
from cinema.models import User

class RegistrationForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
	submit = SubmitField('Sign Up')

	def validate_username(self, username):	# check if username is already in DB
		user = User.query.filter_by(username=username.data).first()
		if user:
			raise ValidationError('That username is taken. Please choose a different one')

	def validate_email(self, email):	# check if email is already in DB
		user = User.query.filter_by(email=email.data).first()
		if user:
			raise ValidationError('That email is taken. Please choose a different one')


class LoginForm(FlaskForm):
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember = BooleanField('Remember Me')
	submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
	email = StringField('Email', validators=[DataRequired(), Email()])
	picture = FileField('Update profile picture', validators=[FileAllowed(['jpg', 'img', 'png'])])
	submit = SubmitField('Update')


	def validate_username(self, username):	# check if username is already in DB
		if username.data != current_user.username:
			user = User.query.filter_by(username=username.data).first()
			if user:
				raise ValidationError('That username is taken. Please choose a different one')

	def validate_email(self, email):	# check if email is already in DB
		if email.data != current_user.email:
			user = User.query.filter_by(email=email.data).first()
			if user:
				raise ValidationError('That email is taken. Please choose a different one')


class EditUser(FlaskForm):
	username = StringField('Search by username:')
	role = StringField('Role')
	search = SubmitField('Search')
	save = SubmitField('Save')

	def validate_username(self, username):	# check if username is already in DB
		user = User.query.filter_by(username=username.data).first()
		if not user:
			raise ValidationError('This user does not exist')


class DeleteUser(FlaskForm):
	username = StringField('Search by username:')
	search = SubmitField('Search')
	delete = SubmitField('Delete')

	def validate_username(self, username):	# check if username is already in DB
		user = User.query.filter_by(username=username.data).first()
		if not user:
			raise ValidationError('This user does not exist')


class CreateUpdateEvent(FlaskForm):
	eventname = StringField('Event name', validators=[DataRequired(), Length(min=5, max=50)])
	event_type = StringField('Event type', validators=[DataRequired(), Length(min=5, max=50)])
	duration = IntegerField(validators=[DataRequired(), NumberRange(min=1, max=400)])
	language = StringField('Language', validators=[DataRequired()])
	age_restriction = IntegerField(validators=[DataRequired(), NumberRange(min=1, max=18)])
	picture = FileField('Upload film picture', validators=[FileAllowed(['jpg', 'img', 'png'])])
	submit = SubmitField('Create')
	update = SubmitField('Update')


class ShowEvents(FlaskForm):
	create = SubmitField('Create')
	update = SubmitField('Update')
	delete = SubmitField('Delete')
