import string
from datetime import datetime, date, timedelta
from flask import redirect, render_template, request, url_for, Blueprint, flash, session
import mysql.connector
from db import db, cursor
from auth import login_required

booking = Blueprint('bookingslot', __name__)


#########################################Copied Code#####################################################
def formatDate(date):
    date = datetime.strptime(date, '%Y-%m-%d')
    formattedDate = date.strftime('%a, %d %b')
    return formattedDate



@booking.route('/bookingslot')
@login_required
def display():

    cursor.execute('''
    SELECT bookingslot.BSlotID,
    bookingslot.date,
    DATE_FORMAT(bookingslot.TimeFrom, '%k:%i') AS TimeFromFormatted,
    DATE_FORMAT(bookingslot.TimeTo, '%k:%i') AS TimeToFormatted,
    owner.Name AS OwnerName,
    vehicle.VehicleNumber FROM bookingslot
    INNER JOIN Owner ON bookingslot.BSlotID = Owner.OwnerID
    INNER JOIN Vehicle ON bookingslot.BSlotID = vehicle.VehicleID''')
    db.commit()
    data = cursor.fetchall()



    Null_query = 'SELECT BSlotID FROM bookingslot WHERE TimeFrom is Null and TimeTo is Null'
    cursor.execute(Null_query)
    NullID = cursor.fetchone()

    return render_template('view/bookingslot.html', data=data, NullID=NullID)


def clearExpiredBookings():
    try:
        current_date = date.today()
        current_time = datetime.now().time()

        # Update expired slots, setting TimeFrom and TimeTo to NULL
        update_query = '''
        UPDATE bookingslot 
        SET TimeFrom = '', TimeTo = '' 
        WHERE date = %s AND TimeTo < %s
        '''

        cursor.execute(update_query, (current_date, current_time))
        db.commit()

        print(f'{cursor.rowcount} expired bookings updated at {datetime.now()}')
    except mysql.connector.Error as e:
        db.rollback()
        print(f'Error updating expired bookings')




@booking.route('/bookingslot/add', methods=['GET', 'POST'])
@login_required
def add_data():
    if request.method == 'POST':
        BSlotID = session.get('VehicleID')
        date = request.form['date']
        TimeFrom = request.form['TimeFrom']
        duration = request.form['duration']
        if not all ((BSlotID or date or TimeFrom or duration)):
            flash('All fields are required')

        try:
            durationStr = int(duration)
        except ValueError as ve:
            flash('duration must be a valid number', 'error')
            return redirect(url_for('bookingslot.add_data'))

        TimeFormat = '%H:%M'
        timeFrom_dt = datetime.strptime(TimeFrom, TimeFormat)
        timeTo_dt = timeFrom_dt + timedelta(hours=durationStr)
        TimeTo = timeTo_dt.strftime(TimeFormat)

        try:
            update_query = '''
                UPDATE bookingslot
                SET date=%s, duration=%s, TimeFrom=%s, TimeTo=%s 
                WHERE BSlotID=%s
            '''
            cursor.execute(update_query, (date,  duration, TimeFrom, TimeTo, BSlotID,))
            db.commit()
            # return render_template('add/owner.html', VehicleID=BSlotID)
        except  mysql.connector.Error as e:
            print(e)
            db.rollback()
            flash('Error adding data')
            return render_template('add/bookingslot.html')
        return redirect(url_for('owner.add_data', VehicleID=BSlotID))
    BSlotID = session.get('VehicleID')
    return render_template('add/bookingslot.html')


@booking.route('/bookingslot/add/<int:BSlotID>')
@login_required
def owner(BSlotID):
    return render_template('add/owner.html', VehicleID=BSlotID)



@booking.route('/bookingslot/edit/<int:BSlotID>', methods=['GET','POST'])
@login_required
def edit_data(BSlotID):
    if request.method == 'POST':
        date = request.form['Date']
        day = request.form['day']
        TimeFrom = request.form['TimeFrom']
        TimeTo = request.form['TimeTo']
        try:
            formattedDate = datetime.strptime(date, '%Y-%m-%d').strftime('%a, %d %b')
            update_query = '''UPDATE bookingslot
                              SET date=%s, day=%s, TimeFrom=%s, TimeTo=%s
                              WHERE BSlotID=%s'''
            cursor.execute(update_query, (date, day, TimeFrom, TimeTo, BSlotID,))
            db.commit()
            return redirect(url_for('bookingslot.display'))
        except mysql.connector.Error as e:
            db.rollback()

    fetch_query = 'SELECT BSlotID, date, day, TimeFrom, TimeTo FROM bookingslot WHERE BSlotID=%s'
    cursor.execute(fetch_query, (BSlotID,))
    db.commit()
    data = cursor.fetchone()
    if data is None:
        flash('Data not found')
        return redirect(url_for('bookingslot.display'))
    data = list(data)
    data[1] = datetime.strptime(data[1], '%Y-%m-%d').strftime('%a, %d %b')
    return render_template('edit/bookingslot.html', data=data)

@booking.route('/bookingslot/delete/<int:BSlotID>', methods=['GET', 'POST'])
@login_required
def delete_data(BSlotID):
    if request.method == 'POST':
        try:
            delete_query = 'DELETE FROM bookingslot WHERE BSlotID=%s'
            cursor.execute(delete_query, (BSlotID,))
            db.commit()
            return redirect(url_for('bookingslot.display'))
        except mysql.connector.Error as e:
            db.rollback()
            flash('Error deleting data')

    fetch_query = 'SELECT BSlotID, date, day, TimeFrom, TimeTo FROM bookingslot WHERE BSlotID=%s'
    cursor.execute(fetch_query, (BSlotID,))
    db.commit()
    data = cursor.fetchone()
    if data is None:
        flash('No data found')
        return redirect(url_for('bookingslot.display'))
    return render_template('delete/bookingslot.html', data=data)

