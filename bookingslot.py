import string
from datetime import datetime, date, timedelta
from flask import redirect, render_template, request, url_for, Blueprint, flash, session
import mysql.connector
from db import db, cursor
from auth import login_required

booking = Blueprint('bookingslot', __name__)

def formatDate(date):
    date = datetime.strptime(date, '%Y-%m-%d')
    formattedDate = date.strftime('%a, %d %b')
    return formattedDate

@booking.route('/bookingslot')
@login_required
def display():
    fetch_query = '''
        SELECT bookingslot.BSlotID,
        bookingslot.date,
        DATE_FORMAT(bookingslot.TimeFrom, '%k:%i') AS TimeFromFormatted,
        DATE_FORMAT(bookingslot.TimeTo, '%k:%i') AS TimeToFormatted,
        owner.Name AS OwnerName,
        vehicle.VehicleNumber,  bookingslot.duration FROM bookingslot
        INNER JOIN Owner ON bookingslot.BSlotID = owner.OwnerID
        INNER JOIN vehicle ON bookingslot.BSlotID = vehicle.VehicleID'''
    cursor.execute(fetch_query)
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
        update_query = '''
        UPDATE bookingslot 
        SET TimeFrom = '', TimeTo = '', duration = '' 
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
        print('Post method mai gaya')
        VehicleID = session.get('VehicleID')
        BSlotID = session.get('VehicleID')
        print(BSlotID, 'BSlotID')
        date = request.form['date']
        TimeFrom = request.form['TimeFrom']
        duration = request.form['duration']
#Always add parameters in the tuple with cursor.execute
        cursor.execute('SELECT SNo FROM vehicle WHERE VehicleID=%s', (VehicleID,))
        db.commit()
        SNo = cursor.fetchone()
        print('fetched SNo', SNo)
        S_No = SNo[0]
        print('SNo in bookingslot: ', S_No)
        
        if not date:
            flash('Please enter date','error')
            return redirect(url_for('bookingslot.add_data', SNo=SNo))
        if not TimeFrom:
            flash('Please enter time to continue','error')
            return redirect(url_for('bookingslot.add_data', SNo=SNo))
        if not duration:
            flash('Please enter duration to continue','error')
            return redirect(url_for('bookingslot.add_data', SNo=SNo))
        if not SNo:
            print('not s no.')
            flash('S_No nahi mil raha bhai','error')
            return redirect(url_for('bookingslot.add_data', SNo=SNo))  
        if not BSlotID:
            flash('Error fetching your BSlotID','error')
            return redirect(url_for('bookingslot.add', SNo=SNo))  
   
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
                SET date=%s, duration=%s, TimeFrom=%s, TimeTo=%s, SNo=%s 
                WHERE BSlotID=%s
            '''
            cursor.execute(update_query, (date,  duration, TimeFrom, TimeTo, S_No, BSlotID,))
            db.commit()
            # return render_template('add/owner.html', VehicleID=BSlotID)
            return redirect(url_for('payment.add_data', VehicleID=BSlotID, S_No=S_No))
        except  mysql.connector.Error as e:
            print(e)
            db.rollback()
            flash('Error adding data')
            return render_template('add/bookingslot.html')
        return redirect(url_for('payment.add_data', VehicleID=BSlotID,S_No=S_No))
    BSlotID = session.get('VehicleID')
    print('BSlotID', BSlotID)
    cursor.execute("SELECT SNo FROM bookingslot WHERE BSlotID=%s", (BSlotID,))
    S = cursor.fetchone()
    SNo = S[0]
    db.commit()
    SID = session.get('incrementedSNo')
    return render_template('add/bookingslot.html', SNo = S[0])

@booking.route('/bookingslot/add/<int:BSlotID>')
@login_required
def payment(BSlotID):
    return render_template('add/owner.html', VehicleID=BSlotID, SNo=SNo)

@booking.route('/bookingslot/edit/<int:BSlotID>', methods=['GET','POST'])
@login_required
def edit_data(BSlotID):
    if request.method == 'POST':
        date = request.form['Date']

        TimeFrom = request.form['TimeFrom']
        TimeTo = request.form['TimeTo']
        try:
            formattedDate = datetime.strptime(date, '%Y-%m-%d').strftime('%a, %d %b')
            update_query = '''UPDATE bookingslot
                              SET date=%s, TimeFrom=%s, TimeTo=%s
                              WHERE BSlotID=%s'''
            cursor.execute(update_query, (date,TimeFrom, TimeTo, BSlotID,))
            db.commit()
            return redirect(url_for('bookingslot.display'))
        except mysql.connector.Error as e:
            db.rollback()

    fetch_query = 'SELECT BSlotID, slot, date, TimeFrom, TimeTo FROM bookingslot WHERE BSlotID=%s'
    cursor.execute(fetch_query, (BSlotID,))
    db.commit()
    data = cursor.fetchone()
    if data is None:
        flash('Data not found')
        return redirect(url_for('bookingslot.display'))
    data = list(data)
    # data[1] = datetime.strptime(data[1], '%Y-%m-%d').strftime('%a, %d %b')
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

