from flask import render_template, url_for, flash, redirect
from cinema import app
from cinema.forms import RegistrationForm, LoginForm
from cinema.models import User


@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html', title='about')


@app.route('/program')
def program():
    return render_template('program.html', title='program')


@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if form.validate_on_submit(): # check if filled data is valid
		if form.email.data == 'admin@cinema.com' and form.password.data == 'password':
			flash('You have been logged in!', 'success')
			return redirect(url_for('home'))
		else:
			flash('Login Unsuccessful. Please check username and password', 'danger')
	return render_template('login.html', title='login', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegistrationForm()
	if form.validate_on_submit(): # check if filled data is valid
		flash(f'{form.username.data}, Thanks for registering!', 'success')
		return redirect(url_for('home'))
	return render_template('register.html', title='register', form=form)
