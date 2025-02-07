import re
import os
import secrets
from datetime import datetime,timedelta
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from cinema import app, db, bcrypt, mail
from cinema.models import User, Event, Date, event_hall, Hall, Seat, Ticket
from cinema.forms import (RegistrationForm, LoginForm, UpdateAccountForm,
	EditUser,DeleteUser, ShowEvents, CreateUpdateEvent, CreateDate,
	DeleteChild, ReserveForUser, RequestResetForm, ResetPasswordForm, ManageUsers, AccountlessReservation)
from cinema.models import User, Event, Date, event_hall, Hall
from flask_login import login_user, current_user, logout_user, login_required
from sqlalchemy import desc, asc
from flask_mail import Message


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
	page = request.args.get('page', 1, type=int)
	dates = Date.query.order_by(asc(Date.date)).paginate(page=page, per_page=5)

	events = Event.query.all() #paginate(page=page, per_page=5)
	halls = Hall.query.all()
	all_halls=[]
	for hall in halls:
		all_halls.append(hall.hall_name)

	if events:
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
	dates = Date.query.all()
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
	return render_template('account.html', title='Account', profile_picture=profile_picture, form=form, dates=dates)


@app.route('/edituser', methods=['GET', 'POST'])
@login_required
def edit_user():
	form = EditUser()
	page = request.args.get('page', 1, type=int)
	users = User.query.order_by(asc(User.id)).paginate(page=page, per_page=10)

	if current_user.role != "Admin":
		abort(403)
	if form.validate_on_submit():
		user_name = form.username.data
		user_role=form.role.data
		user = User.query.filter_by(username=user_name).first()
		try:
			if request.form['search']:
				form.role.data = user.role
		except KeyError:
			pass
		try:
			if request.form['save']:
				user.role = form.role.data
				db.session.commit()
				users = User.query.order_by(asc(User.id)).paginate(page=page, per_page=10)
				form.username.data = ""
				flash('Updated successfully', 'success')
				return render_template('edituser.html', form=form, users=users)
		except KeyError:
			pass
		return render_template('edituser.html', user_name=user_name, user_email=user.email, form=form, user_role=user.role)

	return render_template('edituser.html', form=form, users = users)


@app.route('/deleteuser', methods=['GET', 'POST'])
@login_required
def delete_user():
	form = DeleteUser()
	page = request.args.get('page', 1, type=int)
	users = User.query.order_by(asc(User.id)).paginate(page=page, per_page=10)

	if current_user.role != "Admin":
		abort(403)
	if form.validate_on_submit():
		user_name = form.username.data
		user = User.query.filter_by(username=user_name).first()
		try:
			if request.form['delete']:
				db.session.delete(user)
				db.session.commit()
				users = User.query.order_by(asc(User.id)).paginate(page=page, per_page=10)
				form.username.data = ""
				flash('Deleted successfully', 'success')
				return render_template('deleteuser.html', form=form, users=users)
		except KeyError:
			pass
		return render_template('deleteuser.html',user_name=user_name, user_email=user.email, user_role=user.role, form=form)
	return render_template('deleteuser.html', form=form, users=users)


@app.route('/program/new', methods=['GET', 'POST'])
@login_required
def create_event():
	form = CreateUpdateEvent()
	if current_user.role != "Admin" and current_user.role != "Redactor":
		abort(403)
	picture_file = url_for('static', filename='profile_picture/default/default_event.jpg')	# default picture for first time
	if form.validate_on_submit():
		try:
			time = re.search("^\d+\s(minutes|hours|days)$", form.duration.data)
			if not time:
				flash('Wrong duration format, please use: <time> minutes|hours|days', 'danger')
				return render_template('createevent.html', picture=picture_file, form=form, legend='Create new event')
			if form.picture.data:	
				picture_file = upload_picture(form.picture.data, True)
				event = Event(name=form.eventname.data, event_type=form.event_type.data, duration=form.duration.data,
					language=form.language.data, age_restriction=form.age_restriction.data, description=form.description.data, picture=picture_file)
			else:
				event = Event(name=form.eventname.data, event_type=form.event_type.data, duration=form.duration.data,
					language=form.language.data, age_restriction=form.age_restriction.data, description=form.description.data)
			db.session.add(event)
			db.session.commit()
			flash('Created successfully', 'success')
			return redirect(url_for('program'))
		except:
			db.session().rollback()
			flash('Event should be unique', 'danger')
	return render_template('createevent.html', picture=picture_file, form=form, legend='Create new event')



@app.route('/program/<int:event_id>',methods=['GET','POST'])
@login_required
def event_Parent(event_id):
	if current_user.role not in ["Admin", "Redactor"]:
		abort(403)
	form=CreateDate()
	delform=DeleteChild()
	parent=True
	event = Event.query.get_or_404(event_id)
	event_picture = url_for('static', filename='profile_picture/' + event.picture)
	if delform.validate_on_submit() and delform.delete.data:
		pass
	if form.validate_on_submit() and form.create.data:
		conflict_old_time = True
		hall_name = Hall(hall_name=form.hall.data)
		if form.date.data < datetime.today():
			conflict_old_time=False
		date= Date(date=form.date.data)
		time=re.search("^\d+(?=\s(minutes|hours|days))",event.duration).group(0)
		value=re.search("(minutes|hours|days)$",event.duration).group(0)

		if value=="minutes":
			time=int(time)*60
		elif value=="hours":
			time=int(time)*3600
		elif value=="days":
			time=int(time)*86400

		HallParent = Hall.query.filter(Hall.hall_name == hall_name.hall_name).first()
		start_dates=[datetime.strptime(existing_date.date, '%Y-%m-%d %H:%M:%S') for existing_date in HallParent.dates_for_hall]
		end_dates=[datetime.strptime(existing_date.end_date,'%Y-%m-%d %H:%M:%S') for existing_date in HallParent.dates_for_hall]
		start_dates.sort()
		end_dates.sort()
		conflict=True
		if not start_dates:
			conflict=False
		elif len(start_dates)==1:
			if end_dates[0]<=date.date or date.date+timedelta(seconds=time)<=start_dates[0]:
				conflict=False
		else:
			for i in range(1,len(start_dates)):
				if end_dates[i-1]<=date.date and date.date+timedelta(seconds=time)<=start_dates[i]:
					conflict=False
					break
				elif start_dates[0]>=date.date+timedelta(seconds=time) or date.date>=end_dates[len(end_dates)-1]:
					conflict=False
					break

		if not conflict and conflict_old_time:
			date.end_date=date.date+timedelta(seconds=time)
			db.session.add(date)
			db.session.add(hall_name)
			HallParent=Hall.query.filter(Hall.hall_name==hall_name.hall_name).first()
			HallParent.dates_for_hall.append(date)
			event.dates_of_event.append(date)
			event.halls_of_event.append(hall_name)
			db.session.commit()
			flash('Added successfully', 'success')
		elif not conflict_old_time:
			flash('You cannot create event in past', 'danger')
		else:
			flash("There isn't an available timeslot for the event.",'danger')

		if current_user.role == "Admin" or current_user.role == "Redactor":
			dates=event.dates_of_event.all()
			halls = event.halls_of_event.all()
			occasions=[]
			for hall,date in zip(halls,dates):
				occasions.append(hall.hall_name+"@"+date.date)
			event_picture = url_for('static', filename='profile_picture/' + event.picture)
			return render_template('event.html', form=form, event=event, occasions=occasions, picture=event_picture, parent=parent,delform=delform )
	else:
		halls = event.halls_of_event.all()
		dates = event.dates_of_event.all()
		occasions = []
		for hall, date in zip(halls, dates):
			occasions.append(hall.hall_name + "@" + date.date)
		event_picture = url_for('static', filename='profile_picture/' + event.picture)
		if dates and halls:
			return render_template('event.html', name=event.name, event=event, occasions=occasions, form=form, picture=event_picture, parent=parent, delform=delform)
		else:
			return render_template('event.html', name=event.name, event=event, occasions=occasions, form=form, picture=event_picture, parent=parent, delform=delform)


@app.route('/program/<int:event_id>/<string:route>',methods=['GET','POST'])
def child_delete(event_id, route):
	route=route.split("@")	# route[0] is deleted hall,  route[1] is deleted time

	event=Event.query.filter(Event.id==event_id).first()
	all_halls = event.halls_of_event.all()
	struct_date = event.dates_of_event.all()  # take dates binded to this hall
	for i in range(0, len(struct_date)):
		try:
			if all_halls[i].hall_name == route[0] and struct_date[i].date == route[1]:
				db.session.delete(all_halls[i])
				db.session.delete(struct_date[i])
				db.session.commit()
				break
		except IndexError:
			pass

	return redirect(url_for('event_Parent', event_id=event_id))


def send_email_with_registration(email, ticket):
	msg = Message('Your reservation', sender='cinemaserver@seznam.cz', recipients=[email])
	seats = ''
	for seat in ticket.tickets_on_seat:
		seats += f"Row: {seat.row} Number: {seat.number}\n"
	msg.body = f'''Thank you for your reservation!\n
Event date: {ticket.date.date}
Seats: {seats}
Price: {ticket.price}
'''
	mail.send(msg)


@app.route('/program/<int:event_id>/<string:hall_color>/<string:event_time>',methods=['GET','POST'])
def event(event_id, hall_color, event_time):
	form=CreateDate()
	form_ReserveForUser = ReserveForUser()
	reserveform=AccountlessReservation()
	event = Event.query.get_or_404(event_id)
	hall_name = Hall(hall_name=form.hall.data)
	halls = hall_name.dates_for_hall
	dates = event.dates_of_event
	seats_status = []

	if reserveform.login.data or reserveform.register.data or reserveform.finish.data:
		if reserveform.login.data:
			return redirect(url_for('login'))
		elif reserveform.register.data:
			return redirect(url_for('register'))
		elif reserveform.email.data:
			if request.form.getlist('seat'):
				seats = request.form.getlist('seat')
				# get indexes for reservation
				row_number = []
				for seat in seats:
					row_number.append(re.split(r'_', seat))
				ticket=Ticket(price=len(seats)*120,email=reserveform.email.data)

				db.session.add(ticket)
				all_seats = Seat.query.all()
				hall = Hall.query.filter(Hall.hall_name == hall_color).first()
				date = Date.query.filter(Date.date == event_time).first()
				for index in row_number:
					for seat in all_seats:
						if int(index[0]) == seat.row and int(index[1]) == seat.number:
							seat.is_busy = "disabled"
							seat.tickets_on_seat.append(ticket)
							ticket.date_id = date.id
							ticket.hall_id = hall.id
							db.session.add(seat)
							break;
				if reserveform.validate_on_submit():
					send_email_with_registration(reserveform.email.data, ticket)
					db.session.commit()
					flash('Reserved successfully', 'success')
					return redirect(url_for('program'))
				else:
					flash('Please input a valid email address.','danger')
		else:
			flash("Authentication or email necessary.",'danger')
	elif form_ReserveForUser.validate_on_submit() and form_ReserveForUser.search_user.data:
		user=User.query.filter(User.email==form_ReserveForUser.search_user.data).first()
		if request.form.getlist('seat'):
			seats = request.form.getlist('seat')
			# get indexes for reservation
			row_number = []
			for seat in seats:
				row_number.append(re.split(r'_', seat))
			all_seats = Seat.query.all()

			if user:
				ticket = Ticket(price=len(seats) * 120, user_id=user.id)
			else:
				ticket=Ticket(price=len(seats)*120,email=form_ReserveForUser.search_user.data)
			db.session.add(ticket)
			hall = Hall.query.filter(Hall.hall_name == hall_color).first()
			date = Date.query.filter(Date.date == event_time).first()
			for index in row_number:
				for seat in all_seats:
					if int(index[0]) == seat.row and int(index[1]) == seat.number:
						seat.is_busy = "disabled"
						seat.tickets_on_seat.append(ticket)
						ticket.date_id = date.id
						ticket.hall_id = hall.id
						db.session.add(seat)
						break;
			db.session.commit()
			flash('Reserved for: '+form_ReserveForUser.search_user.data+' successfully', 'success')
			return redirect(url_for('program'))

	else:
		if (form.validate_on_submit() and form.reserve.data):
			if not current_user.is_authenticated:
				flash('Before reservation you need to create account', 'warning')
				return redirect(url_for('register'))
			if request.form.getlist('seat'):
				seats = request.form.getlist('seat')
				# get indexes for reservation
				row_number = []
				for seat in seats:
					row_number.append(re.split(r'_', seat))

				all_seats = Seat.query.all()
				ticket = Ticket(price=len(seats)*120, user_id=current_user.id )	# let's define prices for halls?
				db.session.add(ticket)
				db.session.commit()

				#db.session.add(current_user)
				hall=Hall.query.filter(Hall.hall_name==hall_color).first()
				date=Date.query.filter(Date.date==event_time).first()
				for index in row_number:
					for seat in all_seats:
						if int(index[0]) == seat.row and int(index[1]) == seat.number:
							seat.is_busy = "disabled"
							seat.tickets_on_seat.append(ticket)
							ticket.date_id = date.id
							ticket.hall_id=hall.id
							db.session.add(seat)
							break;
				db.session.commit()
			flash('Reserved successfully', 'success')
			return redirect(url_for('program'))


	event_picture = url_for('static', filename='profile_picture/' + event.picture)
	hall = Hall.query.filter(Hall.hall_name == hall_color).first()
	date = Date.query.filter(Date.date == event_time).first()
	tickets = Ticket.query.filter(Ticket.date_id == date.id).filter(Ticket.hall_id == hall.id).all()
	#Todo very slow implementation. We lose like a second or two to the cycles here.
	for seat in Seat.query.all():
		found=False
		if not tickets:
			seat.is_busy = ""
			db.session.commit()
		elif not seat.tickets_on_seat:
			seat.is_busy = ""
			db.session.commit()
		else:
			for ticket in tickets:
				if found:
					break
				else:
					for ticket_id in seat.tickets_on_seat:
						if ticket_id.id==ticket.id:
							seat.is_busy="disabled"
							db.session.commit()
							found=True
							break
						else:
							seat.is_busy=""
							db.session.commit()

	all_seats = [seat.is_busy for seat in Seat.query.all()]
	row_1 = all_seats[0:6]
	row_2 = all_seats[6:12]
	row_3 = all_seats[12:18]
	seats_status.append(row_1)
	seats_status.append(row_2)
	seats_status.append(row_3)

	return render_template('event.html', name=event.name, event=event, hall=halls, form=form, dates=dates, hall_color=hall_color,
		picture=event_picture, event_time=event_time, seats_status=seats_status, form_ReserveForUser=form_ReserveForUser,reserveform=reserveform)


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
		time=re.search("^\d+\s(minutes|hours|days)$",event.duration)
		if not time:
			flash('Wrong duration format, please use: <time> minutes|hours|days','danger')
		else:
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
	dates = Date.query.all()
	delete_date = []
	if dates:
		for date in dates:
			if date.alldates[0].name == event.name:
				delete_date.append(date)
	

	for date in delete_date:
		Date.query.filter_by(id=date.id).delete()
	db.session.commit()

	db.session.delete(event)
	db.session.commit()
	flash('Your event has been deleted!', 'success')
	return redirect(url_for('program'))


@app.route('/account/deletereservation/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def delete_reservation(ticket_id):
	ticket = Ticket.query.get_or_404(ticket_id)
	ticket.tickets_on_seat.clear()
	db.session.commit()
	db.session.delete(ticket)
	db.session.commit()

	return redirect(url_for('account'))


@app.route('/account/deletereservationbyemployee/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def delete_reservation_by_employee(ticket_id):
	ticket = Ticket.query.get_or_404(ticket_id)
	ticket.tickets_on_seat.clear()
	db.session.commit()
	db.session.delete(ticket)
	db.session.commit()
	flash('Reservation was deleted!', 'success')
	return redirect(url_for('manage_reservations'))


def send_reset_email(user):
	token = user.get_reset_token()
	msg = Message('Password Reset Request', sender='cinemaserver@seznam.cz', recipients=[user.email])
	msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

It you didn't make this request then ignore this email and no changes will be made.
'''
	mail.send(msg)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RequestResetForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		send_reset_email(user)
		flash('An email has been sent with instructions to reset your password', 'info')
		return redirect(url_for('login'))
	return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	user = User.verify_reset_token(token)
	if user is None:
		flash('That is an invalid or expired token', 'warning')
		return redirect(url_for('reset_request'))
	form = ResetPasswordForm()
	if form.validate_on_submit():  # check if filled data is valid
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')  # hash password for user
		user.password = hashed_password
		db.session.commit()
		flash('Your password has been updated!', 'success')
		return redirect(url_for('login'))
	return render_template('reset_token.html', title='Reset Password', form=form)


@app.route("/manage_reservations", methods=['GET', 'POST'])
@login_required
def manage_reservations():
	form = ManageUsers()
	if current_user.role not in ["Admin", "Cashier"]:
		abort(403)
	events = Event.query.all()
	users = User.query.all()
	dates = Date.query.all()
	info = []

	if form.validate_on_submit():
		if form.date.data:	# Search by name of hall and date
			search_by_name_time = True
			if form.date.data < datetime.today():
				flash('You cannot search reservations in past', 'danger')
				return render_template('manage_reservations.html', title='Manage users', form=form)

			tickets = Ticket.query.all()
			for ticket in tickets:
				if datetime.strptime(ticket.date.date, '%Y-%m-%d %H:%M:%S') == form.date.data and ticket.hall.hall_name == form.hall.data:
					tmp = []
					if ticket.user_id == None:
						tmp.append(ticket.email)		
					else:
						user = User.query.get(ticket.user_id)
						tmp.append(user.email)

					tmp.append(ticket)
					info.append(tmp)

		else:	# Search by hall name
			search_by_name_time = False
			tickets = Ticket.query.all()
			for ticket in tickets:
				if ticket.hall.hall_name == form.hall.data:
					tmp = []
					if ticket.user_id == None:
						tmp.append(ticket.email)
					else:
						user = User.query.get(ticket.user_id)
						tmp.append(user.email)

					tmp.append(ticket)
					info.append(tmp)
		return render_template('manage_reservations.html', title='Manage users', form=form, tickets=info, dates=dates, 
				events=events, search_by_name_time=search_by_name_time, hall=form.hall.data)

	return render_template('manage_reservations.html', title='Manage users', form=form)