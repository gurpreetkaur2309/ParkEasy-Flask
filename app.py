from flask import Flask, render_template, session
from vehicle import Vehicle
from slots import slots
from owner import owner
from sensor import sensor
from bookingslot import booking
from payment import payment
from auth import auth
from bookingslot import clearExpiredBookings
from apscheduler.schedulers.background import BackgroundScheduler
import logging

app = Flask(__name__)
app.secret_key = 'kjasdfhoiuehsfowe9phif9824ye8972hwuiefohnsdfp'

@app.route('/')
def index():
    return render_template("index.html")
app.register_blueprint(Vehicle)
app.register_blueprint(slots)
app.register_blueprint(owner)
app.register_blueprint(sensor)
app.register_blueprint(booking)
app.register_blueprint(payment)
app.register_blueprint(auth)

@app.context_processor
def inject_user():
    username = session.get('username')
    SNo = session.get('SNo')
    return dict(username=username)


def configure_scheduler():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=clearExpiredBookings, trigger="interval", minutes=5)
    scheduler.start()
    logging.info("Scheduler started to clear expired bookings every 5 minutes.")

configure_scheduler()
if __name__ == '__main__':
    app.run(debug=True, port='5000')


