from flask import render_template
from cinema import app, db

@app.errorhandler(404)
def error_404(error):
	return render_template('errors/404.html'), 404


@app.errorhandler(403)
def error_403(error):
	return render_template('errors/403.html'), 403


@app.errorhandler(500)
def error_500(error):
	return render_template('errors/500.html'), 500

@app.errorhandler(413)
def error_413(error):
	return render_template('errors/413.html'), 413