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
        SELECT b.BSlotID, 
               if(b.date is null, '', b.date) as formatted_Date,
               if(b.TimeFrom = '00:00:00', '', b.TimeFrom) as formatted_timeFrom, 
               if(b.TimeTo = '00:00:00', '', b.TimeTo) as formatted_timeTo, 
               b.duration,
               v.VehicleNumber
        FROM bookingslot b  
        JOIN vehicle v ON b.BSlotID = v.VehicleID 
        '''
    cursor.execute(fetch_query)
    db.commit()
    data = cursor.fetchall()
    Null_query = 'SELECT BSlotID FROM bookingslot WHERE TimeFrom is Null and TimeTo is Null'
    cursor.execute(Null_query)
    NullID = cursor.fetchone()
    return render_template('view/bookingslot.html', data=data, NullID=NullID)

@booking.route('/history')
@login_required
def history():
    fetch_query = '''
        SELECT VehicleID, username, date, TimeFrom, TimeTo, duration, name, contact, TotalPrice, mode, VehicleType, VehicleNumber FROM allotment
    '''
    cursor.execute(fetch_query)
    db.commit()
    data = cursor.fetchall()
    return render_template('view/history.html', data=data)

# def clearExpiredBookings():
#     try:
#         current_date = date.today()
#         current_time = datetime.now().time()
#         update_query = '''
#         UPDATE bookingslot b 
#         INNER JOIN payment p ON b.BSlotID = p.PaymentID
#         INNER JOIN vehicle v ON b.BSlotID = v.VehicleID
#         INNER JOIN sensor s ON b.BSlotID = s.SensorID
#         SET b.TimeFrom = '', b.TimeTo = '', b.duration = '', b.date = null,
#             p.TotalPrice = 0, p.mode = '',
#             s.isParked=0
#         WHERE b.date < %s OR b.TimeTo < %s
#         '''
#         cursor.execute(update_query, (current_date, current_time))
#         db.commit()
#         print(f'{cursor.rowcount} expired bookings updated at {datetime.now()}')
#     except mysql.connector.Error as e:
#         db.rollback()
#         print(f'Error updating expired bookings')

@booking.route('/bookingslot/add', methods=['GET', 'POST'])
@login_required
def add_data():
    print(session['username'])
    VehicleID = request.args.get('VehicleID')
    print('VehicleID: ', VehicleID)
    VacantSlots = '''
            SELECT b.BSlotID FROM bookingslot b 
            WHERE b.TimeFrom = "00:00:00" and b.TimeTo = "00:00:00" and b.duration= '';
        '''
    cursor.execute(VacantSlots)
    db.commit()
    BSlotID = cursor.fetchone()[0]
    print('BSlotID: ', BSlotID)
    

    if request.method == 'POST':
        VehicleID = session.get('VehicleID')
        print('VehicleID: ', VehicleID)
        if not VehicleID:
            flash('An error occurred. Please try again later','error')
            return redirect(url_for('bookingslot.add_data', VehicleID=VehicleID, SNo=SNo))
        
        print('BSlotID: ', BSlotID)
        date = request.form['date']
        TimeFrom = request.form['TimeFrom']
        duration = request.form['duration']
        cursor.execute('SELECT SNo FROM vehicle WHERE VehicleID=%s', (VehicleID,))
        db.commit()
        SNo = cursor.fetchone()
        S_No = SNo[0]
        if not SNo:
            flash('An error occurred. Please try again later','error')
            return  redirect(url_for('bookingslot.add_data', VehicleID=VehicleID, SNo=SNo))
        print(SNo, 'SNo in bookingslot')
        if not date:
            flash('Please enter date','error')
            return redirect(url_for('bookingslot.add_data',VehicleID=VehicleID, SNo=SNo))
        if not TimeFrom:
            flash('Please enter time to continue','error')
            return redirect(url_for('bookingslot.add_data',VehicleID=VehicleID, SNo=SNo))
        if not duration:
            flash('Please enter duration to continue','error')
            return redirect(url_for('bookingslot.add_data',VehicleID=VehicleID, SNo=SNo))
        if not SNo:
            print('not s no.')
            flash('S_No nahi mil raha bhai','error')
            return redirect(url_for('bookingslot.add_data',VehicleID=VehicleID, SNo=SNo))  
        if not BSlotID:
            flash('Error fetching your BSlotID','error')
            return redirect(url_for('bookingslot.add',VehicleID=VehicleID, SNo=SNo))  
              
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
            #debugging
            cursor.execute('SELECT date,  duration, TimeFrom, TimeTo, SNo, BSlotID FROM bookingslot WHERE BSlotID=%s',(BSlotID,))
            db.commit()
            data = cursor.fetchone()
            #end
            return redirect(url_for('payment.add_data', VehicleID=BSlotID, SNo=S_No))
        except  mysql.connector.Error as e:
            print(e)
            db.rollback()
            flash('Error adding data')
            return render_template('add/bookingslot.html')
        return redirect(url_for('payment.add_data', VehicleID=BSlotID,SNo=S_No))
    cursor.execute("SELECT SNo FROM bookingslot WHERE BSlotID=%s", (BSlotID,))
    S = cursor.fetchone()
    db.commit()
    if S == None:
        flash('An error occured. Please try again later.', 'error')
        return redirect(url_for('bookingslot.add_data', VehicleID=VehicleID))
    SNo = S[0]

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

