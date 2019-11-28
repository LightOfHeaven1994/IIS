import re
import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from cinema import app, db, bcrypt
from cinema.forms import RegistrationForm, LoginForm, UpdateAccountForm, EditUser, DeleteUser, ShowEvents, CreateUpdateEvent, CreateDate
from cinema.models import User, Event, Date, event_hall, Hall, Seat, Ticket
from cinema.forms import RegistrationForm, LoginForm, UpdateAccountForm, EditUser, DeleteUser, ShowEvents, CreateUpdateEvent, CreateDate, DeleteChild
from cinema.models import User, Event, Date, event_hall, Hall
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import desc, asc


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
	dates = Date.query.order_by(asc(Date.date))

	events = Event.query.all()
	halls = Hall.query.all()
	all_halls=[]
	for hall in halls:
		all_halls.append(hall.hall_name)

	if events:
		print("SEND DATA")
		return render_template('program.html', title='program', events=events, dates=dates, halls=all_halls, form=form)
	else:
		return render_template('program.html', title='program', halls=all_halls, form=form)



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


def upload_picture(form_picture, is_event_pic):  # generate random name for pic and save it
	random_hex = secrets.token_hex(8)
	_, f_ext = os.path.splitext(form_picture.filename)
	picture_name = random_hex + f_ext
	picture_path = os.path.join(app.root_path, 'static/profile_picture', picture_name)

	size = 255, 255
	if is_event_pic:
		size = 512, 512
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
		if form.password.data:
			hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')  # hash password for user
			current_user.password = hashed_password
		if form.picture.data:
			picture_file = upload_picture(form.picture.data, False)
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
				return render_template('edituser.html', form=form)
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


@app.route('/program/new', methods=['GET', 'POST'])
@login_required
def create_event():
	form = CreateUpdateEvent()
	if current_user.role != "Admin" and current_user.role != "Redactor":
		abort(403)
	picture_file = url_for('static', filename='profile_picture/default_event.jpg')	# default picture for first time
	if form.validate_on_submit():
		try:
			if form.picture.data:	
				picture_file = upload_picture(form.picture.data, True)
			event = Event(name=form.eventname.data, event_type=form.event_type.data, duration=form.duration.data,
				language=form.language.data, age_restriction=form.age_restriction.data, description=form.description.data, picture=picture_file)
			db.session.add(event)
			db.session.commit()
			flash('Created successfully', 'success')
			return redirect(url_for('program'))
		except:
			db.session().rollback()
			flash('Event should be unique', 'danger')
	return render_template('createevent.html', picture=picture_file, form=form, legend='Create new event')



@app.route('/program/<int:event_id>',methods=['GET','POST'])
def event_Parent(event_id):
	form=CreateDate()
	delform=DeleteChild()
	parent=True
	event = Event.query.get_or_404(event_id)
	event_picture = url_for('static', filename='profile_picture/' + event.picture)
	if delform.validate_on_submit() and delform.delete.data:
		pass
	if form.validate_on_submit() and form.create.data:
		hall_name = Hall(hall_name=form.hall.data)
		date= Date(date=form.date.data)
		db.session.add(date)
		db.session.add(hall_name)
		hall_name.dates_for_hall.append(date)
		event.dates_of_event.append(date)
		event.halls_of_event.append(hall_name)
		db.session.commit()
		flash('Added successfully', 'success')
		if current_user.role == "Admin" or current_user.role == "Redactor":
			dates=event.dates_of_event.all()
			halls = event.halls_of_event.all()
			occasions=[]
			for hall,date in zip(halls,dates):
				occasions.append(hall.hall_name+"/"+date.date)
			event_picture = url_for('static', filename='profile_picture/' + event.picture)
			return render_template('event.html', form=form, event=event, occasions=occasions, picture=event_picture, parent=parent,delform=delform )
	else:
		halls = event.halls_of_event.all()
		dates = event.dates_of_event.all()
		occasions = []
		for hall, date in zip(halls, dates):
			occasions.append(hall.hall_name + "/" + date.date)
		event_picture = url_for('static', filename='profile_picture/' + event.picture)
		if dates and halls:
			return render_template('event.html', name=event.name, event=event, occasions=occasions, form=form, picture=event_picture, parent=parent, delform=delform)
		else:
			return render_template('event.html', name=event.name, event=event, occasions=occasions, form=form, picture=event_picture, parent=parent, delform=delform)


@app.route('/program/<int:event_id>/<string:route>',methods=['GET','POST'])
def child_delete(event_id,route):
	route=route.split("/")
	print(route[0]+route[1]+"WTF?")
	sql='DELETE FROM Hall NATURAL JOIN "Date" WHERE "Date".date=%s AND Hall.name=%s'
	db.engine.execute(sql,route[1],route[0],())
	return render_template('layout.html')

@app.route('/program/<int:event_id>/<string:hall_color>/<string:event_time>',methods=['GET','POST'])
def event(event_id, hall_color, event_time):
	form=CreateDate()
	event = Event.query.get_or_404(event_id)
	hall_name = Hall(hall_name=form.hall.data)
	halls = hall_name.dates_for_hall
	dates = event.dates_of_event
	seats_status = []

	if form.validate_on_submit():
		if not current_user.is_authenticated:
			flash('Before reservation you need to create account', 'warning')
			return redirect(url_for('register'))

		print("\n\nSeats:")
		if request.form.getlist('seat'):
			seats = request.form.getlist('seat')
			print(seats)
			# get indexes for reservation
			row_number = []
			for seat in seats:
				row_number.append(re.split(r'_', seat))

			all_seats = Seat.query.all()
			ticket = Ticket(price=len(seats)*120, user_id=current_user.id)	# let's define prices for halls?
			db.session.add(ticket)
			db.session.commit()

			db.session.add(current_user)
			for index in row_number:
				for seat in all_seats:
					if int(index[0]) == seat.row and int(index[1]) == seat.number:
						seat.is_busy = "disabled"
						seat.ticket_id = ticket.id
						print("TRY ADD TICKET")
						print(ticket.id)
						db.session.add(seat)
						break;
			db.session.commit()


		flash('Reserved successfully', 'success')
		return redirect(url_for('program'))

	print("HOW MANY TICKETS DO I HAVE")
	#print(current_user.tickets)

	# if(current_user.tickets):
	# 	print("TICKET PRICE")
	# 	print(current_user.tickets[0].price)
	# 	print("HOW MANY SEATS HAVE TICKET")
	# 	print(current_user.tickets[0].seats)

	event_picture = url_for('static', filename='profile_picture/' + event.picture)

	all_seats = [seat.is_busy for seat in Seat.query.all()]
	row_1 = all_seats[0:6]
	row_2 = all_seats[6:12]
	row_3 = all_seats[12:18]
	seats_status.append(row_1)
	seats_status.append(row_2)
	seats_status.append(row_3)


	return render_template('event.html', name=event.name, event=event, hall=halls, form=form, dates=dates, hall_color=hall_color,
		picture=event_picture, event_time=event_time, seats_status=seats_status)


@app.route('/program/<int:event_id>/update', methods=['GET', 'POST'])
@login_required
def update_event(event_id):
	event = Event.query.get_or_404(event_id)
	if current_user.role != "Admin" and current_user.role != "Redactor":
		abort(403)
	form = CreateUpdateEvent()
	if form.validate_on_submit():
		event.name = form.eventname.data
		event.event_type = form.event_type.data
		event.duration = form.duration.data
		event.language = form.language.data
		event.age_restriction = form.age_restriction.data
		event.description = form.description.data

		if form.picture.data:
			picture_file = upload_picture(form.picture.data, True)
			event.picture = picture_file
		db.session.commit()
		flash('Your event has been updated!', 'success')
		return redirect(url_for('event_Parent', event_id=event.id, hall_color='Default', event_time='0000-00-00 00:00'))
	elif request.method == 'GET':
		form.eventname.data = event.name
		form.event_type.data = event.event_type
		form.duration.data = event.duration
		form.language.data = event.language
		form.age_restriction.data = event.age_restriction
		form.description.data = event.description
	event_picture = url_for('static', filename='profile_picture/' + event.picture)
	return render_template('createevent.html', form=form, picture=event_picture, legend='Update event') #


@app.route('/program/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
	event = Event.query.get_or_404(event_id)
	if current_user.role != "Admin" and current_user.role != "Redactor":
		abort(403)
	db.session.delete(event)
	db.session.commit()
	flash('Your event has been deleted!', 'success')
	return redirect(url_for('program'))
