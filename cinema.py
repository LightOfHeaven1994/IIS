from flask import Flask, render_template, url_for, flash, redirect
from forms import RegistrationForm, LoginForm


app = Flask(__name__)
app.config['SECRET_KEY'] = '7749a40aa6e1e5d1b179d879aef51844'


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


if __name__ == '__main__':
	app.run(debug=True)
