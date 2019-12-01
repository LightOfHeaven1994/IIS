import re
import os
import secrets
from datetime import datetime,timedelta
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from cinema import app, db, bcrypt
from cinema.forms import RegistrationForm, LoginForm, UpdateAccountForm, EditUser, DeleteUser, ShowEvents, CreateUpdateEvent, CreateDate
from cinema.models import User, Event, Date, event_hall, Hall, Seat, Ticket
from cinema.forms import RegistrationForm, LoginForm, UpdateAccountForm, EditUser, DeleteUser, ShowEvents, CreateUpdateEvent, CreateDate, DeleteChild, ReserveForUser
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
	page = request.args.get('page', 1, type=int)
	dates = Date.query.order_by(asc(Date.date)).paginate(page=page, per_page=5)

	events = Event.query.all() #paginate(page=page, per_page=5)
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
	picture_file = url_for('static', filename='profile_picture/default/default_event.jpg')	# default picture for first time
	if form.validate_on_submit():
		try:
			event = Event(name=form.eventname.data, event_type=form.event_type.data, duration=form.duration.data,
				language=form.language.data, age_restriction=form.age_restriction.data, description=form.description.data)
			if form.picture.data:	
				picture_file = upload_picture(form.picture.data, True)
				event.picture_file = picture_file
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

		if not conflict:
			date.end_date=date.date+timedelta(seconds=time)
			db.session.add(date)
			db.session.add(hall_name)
			HallParent=Hall.query.filter(Hall.hall_name==hall_name.hall_name).first()
			HallParent.dates_for_hall.append(date)
			event.dates_of_event.append(date)
			event.halls_of_event.append(hall_name)
			db.session.commit()
			flash('Added successfully', 'success')
		else:
			flash("There isn't an available timeslot for the event.",'danger')

		if current_user.role == "Admin" or current_user.role == "Redactor":
			dates=event.dates_of_event.all()
			halls = event.halls_of_event.all()
			occasions=[]
			for hall,date in zip(halls,dates):
				occasions.append(hall.hall_name+"&"+date.date)
			event_picture = url_for('static', filename='profile_picture/' + event.picture)
			return render_template('event.html', form=form, event=event, occasions=occasions, picture=event_picture, parent=parent,delform=delform )
	else:
		halls = event.halls_of_event.all()
		dates = event.dates_of_event.all()
		occasions = []
		for hall, date in zip(halls, dates):
			occasions.append(hall.hall_name + "&" + date.date)
		event_picture = url_for('static', filename='profile_picture/' + event.picture)
		if dates and halls:
			return render_template('event.html', name=event.name, event=event, occasions=occasions, form=form, picture=event_picture, parent=parent, delform=delform)
		else:
			return render_template('event.html', name=event.name, event=event, occasions=occasions, form=form, picture=event_picture, parent=parent, delform=delform)


@app.route('/program/<int:event_id>/<string:route>',methods=['GET','POST'])
def child_delete(event_id, route):
	route=route.split("&")	# route[0] is deleted hall,  route[1] is deleted time

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


@app.route('/program/<int:event_id>/<string:hall_color>/<string:event_time>',methods=['GET','POST'])
def event(event_id, hall_color, event_time):
	form=CreateDate()
	form_ReserveForUser = ReserveForUser()
	event = Event.query.get_or_404(event_id)
	hall_name = Hall(hall_name=form.hall.data)
	halls = hall_name.dates_for_hall
	dates = event.dates_of_event
	seats_status = []

	if form.validate_on_submit() or (form_ReserveForUser.validate_on_submit() and request.form_ReserveForUser['inputEmail']):
		print(form.validate_on_submit())
		if not current_user.is_authenticated:
			flash('Before reservation you need to create account', 'warning')
			return redirect(url_for('register'))
		print(request.form)
		print("\n\nSeats:")
		if request.form.getlist('seat'):
			seats = request.form.getlist('seat')
			print(seats)
			# get indexes for reservation
			row_number = []
			for seat in seats:
				row_number.append(re.split(r'_', seat))

			all_seats = Seat.query.all()
			ticket = Ticket(price=len(seats)*120, user_id=current_user.id )	# let's define prices for halls?
			#TODO add all seats of a ticket here later
			db.session.add(ticket)
			db.session.commit()

			db.session.add(current_user)
			hall=Hall.query.filter(Hall.hall_name==hall_color).first()
			date=Date.query.filter(Date.date==event_time).first()
			for index in row_number:
				for seat in all_seats:
					if int(index[0]) == seat.row and int(index[1]) == seat.number:
						seat.is_busy = "disabled"
						seat.tickets_on_seat.append(ticket)
						ticket.date_id = date.id
						ticket.hall_id=hall.id
						print("TRY ADD TICKET")
						print(ticket.id)
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
		picture=event_picture, event_time=event_time, seats_status=seats_status, form_ReserveForUser=form_ReserveForUser)


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
		time=re.search("^\d+(?=\s(minutes|hours|days))",event.duration)
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
	print(ticket.tickets_on_seat)
	ticket.tickets_on_seat.clear()
	db.session.commit()
	db.session.delete(ticket)
	db.session.commit()

	return redirect(url_for('account'))
