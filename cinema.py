from flask import Flask, render_template, url_for
app = Flask(__name__)


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

@app.route('/login')
def login():
    return render_template('login.html', title='login')


@app.route('/register')
def register():
    return render_template('register.html', title='register')


if __name__ == '__main__':
	app.run(debug=True)
