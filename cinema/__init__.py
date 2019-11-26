from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = '7749a40aa6e1e5d1b179d879aef51844'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from cinema import routes



# CREATE EVERYTHING FOR US.@@@@@@@@@@@@@@@@@@@@@@@@@@@
from cinema.models import User, Event, Hall, Seat
db.drop_all()
db.create_all()

halls = ['Green Hall', 'Red Hall', 'Blue Hall']

for i in halls:
	hall = Hall(hall_name=i)
	db.session.add(hall)

for y in range(3):
	for i in range(3):
		seat = Seat(row=y, number=i, hall_id=1)
		db.session.add(seat)

hashed_password = bcrypt.generate_password_hash("admin").decode('utf-8')  # hash password for user
user = User(username="admin", email="admin@admin.com", password=hashed_password, role="Admin")
db.session.add(user)

hashed_password = bcrypt.generate_password_hash("test").decode('utf-8')  # hash password for user
user_1 = User(username="test", email="test@test.com", password=hashed_password, role="User")
db.session.add(user_1)

event = Event(name="Zamyla oznuk", event_type="Bye bye party", duration=120, language="kz", age_restriction=18)
db.session.add(event)

db.session.commit()

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
