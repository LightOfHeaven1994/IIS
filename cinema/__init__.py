from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from datetime import timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = '7749a40aa6e1e5d1b179d879aef51844'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
db = SQLAlchemy(app)

bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
app.config['MAIL_SERVER'] = 'smtp.seznam.cz'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'cinemaserver@seznam.cz'
app.config['MAIL_PASSWORD'] = 'iisCinemaServer'
mail = Mail(app)
# cinemaserver@seznam.cz
# iisCinemaServer

from cinema import routes, errors



# @@@@@@@@@@@@@@@@@@  INIT  @@@@@@@@@@@@@@@@@@@@@@@@@@@

from cinema.models import User, Event, Hall, Seat

db.drop_all()
db.create_all()

halls = ['Green Hall', 'Red Hall', 'Blue Hall']

for i in halls:
	hall = Hall(hall_name=i)
	db.session.add(hall)

# initialize 6 seats 3 rows
for y in range(1, 4):
	for i in range(1, 7):
		seat = Seat(row=y, number=i, hall_id=1, is_busy="")
		db.session.add(seat)

for y in range(1, 4):
	for i in range(1, 7):
		seat = Seat(row=y, number=i, hall_id=2, is_busy="")
		db.session.add(seat)

for y in range(1, 4):
	for i in range(1, 7):
		seat = Seat(row=y, number=i, hall_id=3, is_busy="")
		db.session.add(seat)

hashed_password = bcrypt.generate_password_hash("admin").decode('utf-8')  # hash password for user
admin = User(username="admin", email="admin@admin.com", password=hashed_password, role="Admin")
db.session.add(admin)

hashed_password = bcrypt.generate_password_hash("user1").decode('utf-8')  # hash password for user
user_1 = User(username="user1", email="user1@user1.com", password=hashed_password, role="User")
db.session.add(user_1)

hashed_password = bcrypt.generate_password_hash("user2").decode('utf-8')  # hash password for user
user_2 = User(username="user2", email="user2@user2.com", password=hashed_password, role="User")
db.session.add(user_2)

hashed_password = bcrypt.generate_password_hash("cashier").decode('utf-8')  # hash password for user
cashier = User(username="cashier", email="cashier@cashier.com", password=hashed_password, role="Cashier")
db.session.add(cashier)

hashed_password = bcrypt.generate_password_hash("redactor").decode('utf-8')  # hash password for user
redactor = User(username="redactor", email="redactor@redactor.com", password=hashed_password, role="Redactor")
db.session.add(redactor)

description = '''Chartam ingenii sed scripti fallere res nec caeteri perduci vis. Scriptura inquirere gi co vi 
extitisse quadratam pertinent. Fecto dubio major jam lor operi miror falsi. Ab automata deveniri facturum 
formemus tollitur si cogitare eo. Ab virorum reliqui at haustam me dicitur ex. '''

event = Event(name ="American history", event_type="Film", duration="120 minutes", language="en", age_restriction=18, description=description)
db.session.add(event)

db.session.commit()

#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
