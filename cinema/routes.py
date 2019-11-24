import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from cinema import app, db, bcrypt
from cinema.forms import RegistrationForm, LoginForm, UpdateAccountForm, EditUser, DeleteUser, ShowEvents, CreateUpdateEvent
from cinema.models import User, Event
from flask_login import login_user, current_user, logout_user, login_required


@app.route('/')
@app.route('/home')
def home():
	return render_template('home.html')


@app.route('/about')
def about():
	return render_template('about.html', title='about')


@app.route('/program')
def program():
	form = ShowEvents()
	if form.validate_on_submit():
		print("CLICK KURVA")
		print("KURVA\nKURVA\n")
		# print(request.form)
		# print("\n\n")
		# try:
		# 	if request.form['create']:
		# 		return redirect(url_for('createevent'))
		# except KeyError:
		# 	pass
		# try:
		# 	if request.form['update']:
		# 		return redirect(url_for('about'))
		# except KeyError:
		# 	pass
		# try:
		# 	if request.form['delete']:
		# 		return redirect(url_for('about'))
		# except KeyError:
		# 	pass
	events = Event.query.all()
	print(events)
	if events:
		return render_template('program.html', title='program', events=events, form=form)
	else:
		return render_template('program.html', title='program', form=form)



@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = LoginForm()
	if form.validate_on_submit():  # check if filled data is valid
		user = User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password, form.password.data):
			login_user(user, remember=form.remember.data)
			next_page = request.args.get('next')
			return redirect(next_page) if next_page else redirect(url_for('home'))
		else:
			flash('Login Unsuccessful. Please check username and password', 'danger')
	return render_template('login.html', title='login', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RegistrationForm()
	if form.validate_on_submit():  # check if filled data is valid
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')  # hash password for user
		user = User(username=form.username.data, email=form.email.data, password=hashed_password)
		db.session.add(user)
		db.session.commit()
		flash(f'{form.username.data}, Thanks for registering!', 'success')
		return redirect(url_for('login'))
	return render_template('register.html', title='register', form=form)


@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('home'))


def upload_picture(form_picture):  # generate random name for pic and save it
	random_hex = secrets.token_hex(8)
	_, f_ext = os.path.splitext(form_picture.filename)
	picture_name = random_hex + f_ext
	picture_path = os.path.join(app.root_path, 'static/profile_picture', picture_name)

	size = 255, 255
	im = Image.open(form_picture)
	im.thumbnail(size)
	im.save(picture_path)

	return picture_name


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
	form = UpdateAccountForm()
	if form.validate_on_submit():
		current_user.username = form.username.data
		current_user.email = form.email.data
		if form.picture.data:
			picture_file = upload_picture(form.picture.data)
			current_user.profile_picture = picture_file
		db.session.commit()
		flash('Your accoun has been updated', 'success')
		return redirect(url_for('account'))
	elif request.method == 'GET':
		form.username.data = current_user.username
		form.email.data = current_user.email
	profile_picture = url_for('static', filename='profile_picture/' + current_user.profile_picture)
	return render_template('account.html', title='Account', profile_picture=profile_picture, form=form)


@app.route('/edituser', methods=['GET', 'POST'])
@login_required
def edit_user():
	form = EditUser()
	if current_user.role != "Admin":
		abort(403)
	if form.validate_on_submit():
		user_name = form.username.data
		user_role=form.role.data
		user = User.query.filter_by(username=user_name).first()
		print(request.form)
		try:
			if request.form['search']:
				form.role.data = user.role
		except KeyError:
			pass
		try:
			if request.form['save']:
				user.role = form.role.data
				db.session.commit()
				form.username.data = ""
				flash('Saved successfully', 'success')
				return render_template('deleteuser.html', form=form)
		except KeyError:
			pass
		return render_template('edituser.html', user_name=user_name, user_email=user.email, form=form,user_role=user.role)

	return render_template('edituser.html', form=form)


@app.route('/deleteuser', methods=['GET', 'POST'])
@login_required
def delete_user():
	form = DeleteUser()
	if current_user.role != "Admin":
		abort(403)
	if form.validate_on_submit():
		user_name = form.username.data
		user = User.query.filter_by(username=user_name).first()
		try:
			if request.form['delete']:
				db.session.delete(user)
				db.session.commit()
				form.username.data = ""
				flash('Deleted successfully', 'success')
				return render_template('deleteuser.html', form=form)
		except KeyError:
			pass
		return render_template('deleteuser.html',user_name=user_name, user_email=user.email, user_role=user.role, form=form)
	return render_template('deleteuser.html', form=form)


@app.route('/createevent', methods=['GET', 'POST'])
@login_required
def create_event():
	form = CreateUpdateEvent()
	if current_user.role != "Admin" and current_user.role != "Redactor":
		abort(403)
	picture_file = url_for('static', filename='profile_picture/default_event.jpg')
	if form.validate_on_submit():
		print("HLEDAM PIC")
		print(form.picture.data)
		if form.picture.data:
			picture_file = upload_picture(form.picture.data)
			print("UPLOAD NEW:" + picture_file)
		print("DEFAULT PIC:" + picture_file)
		event = Event(name=form.eventname.data, event_type=form.event_type.data, duration=form.duration.data, 
			language=form.language.data, age_restriction=form.age_restriction.data, picture=picture_file)
		db.session.add(event)
		db.session.commit()
		flash('Created successfully', 'success')
	return render_template('createevent.html', title='createevent', picture=picture_file, form=form)


# @app.route('/updateevent', methods=['GET', 'POST'])
# @login_required
# def update_event():
# 	form = CreateUpdateEvent()
# 	if current_user.role != "Admin" and current_user.role != "Redactor":
# 		abort(403)
# 	if form.validate_on_submit():
# 		# current_user.username = form.username.data
# 		# current_user.email = form.email.data
# 		# if form.picture.data:
# 		# 	picture_file = upload_picture(form.picture.data)
# 		# 	current_user.profile_picture = picture_file
# 		# db.session.commit()
# 		# flash('Your accoun has been updated', 'success')
# 		# return redirect(url_for('account'))
# 	elif request.method == 'GET':
		
# 		# form.username.data = current_user.username
# 		# form.email.data = current_user.email
# 	return render_template('updateevent.html', title='updateevent', form=form)

