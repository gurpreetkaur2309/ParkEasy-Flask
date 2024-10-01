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
#         SET b.TimeFrom = '', b.TimeTo = '', b.duration = '', b.date = '00:00:00',
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
    vid = session.get('VehicleID')
    print('Session wali vehicleID', vid)
    print('bookingslot wale add_data mai gaya')
    print(session['username'])
    VehicleID = request.args.get('VehicleID')
    session['VehicleID'] = VehicleID
    print('VehicleID: ', VehicleID)
    print('vacantslots k upar')
    VacantSlots = '''
            SELECT b.BSlotID FROM bookingslot b 
            WHERE b.TimeFrom = "00:00:00" and b.TimeTo = "00:00:00" and b.duration= '';
        '''
    cursor.execute(VacantSlots)
    db.commit()
    BSlotID = cursor.fetchone()[0]
    session['BSlotID'] = BSlotID
    print('vacantslots k niche')
    print('BSlotID: ', BSlotID)

    
    print('post method k upar')
    if request.method == 'POST':
        VehicleID = request.form.get('VehicleID')
        print('post method k andar')

        print('VehicleID in post method', VehicleID)
        if not VehicleID:
            print('if not vehicleID mai gaya')
            # flash('An error occurred. Please try again later','error')
            return redirect(url_for('bookingslot.add_data', VehicleID=VehicleID, BSlotID=BSlotID))
        
        print('BSlotID: ', BSlotID)
        date = request.form['date']
        TimeFrom = request.form['TimeFrom']
        duration = request.form['duration']
        print('Sno from vehicle k upar')
        cursor.execute('SELECT SNo FROM vehicle WHERE VehicleID=%s', (VehicleID,))
        db.commit()
        SNo = cursor.fetchone()
        S_No = SNo[0]
        if not SNo:
            # flash('An error occurred. Please try again later','error')
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
        print('sare if not k niche') 
        try:
            durationStr = int(duration)
        except ValueError as ve:
            flash('duration must be a valid number', 'error')
            return redirect(url_for('bookingslot.add_data', VehicleID=VehicleID, SNo=SNo))

        TimeFormat = '%H:%M'
        timeFrom_dt = datetime.strptime(TimeFrom, TimeFormat)
        timeTo_dt = timeFrom_dt + timedelta(hours=durationStr)
        TimeTo = timeTo_dt.strftime(TimeFormat)
        print('VehicleID: ', VehicleID)

        print('update query wale try k upar')
        try:
            print('update query wale try k andar')
            update_query = '''
                UPDATE bookingslot
                SET date=%s, duration=%s, TimeFrom=%s, TimeTo=%s, SNo=%s, VehicleID=%s
                WHERE BSlotID=%s
            '''
            cursor.execute(update_query, (date,  duration, TimeFrom, TimeTo, S_No, VehicleID, BSlotID,))
            db.commit()
            # return render_template('add/owner.html', VehicleID=BSlotID)
            #debugging
            data = cursor.fetchone()
            #end
            return redirect(url_for('payment.add_data', VehicleID=VehicleID, SNo=S_No))
        except  mysql.connector.Error as e:
            print('update query wale except k andar')
            print(e)
            db.rollback()
            flash('Error adding data')
            return render_template('add/bookingslot.html')
        print('VehicleID: ', VehicleID)
        return redirect(url_for('payment.add_data', SNo=S_No, VehicleID=VehicleID))
    cursor.execute("SELECT SNo FROM bookingslot WHERE BSlotID=%s", (BSlotID,))
    S = cursor.fetchone()
    db.commit()
    if S == None:
        print('if not S k andar')
        # flash('An error occured. Please try again later.', 'error')
        return redirect(url_for('bookingslot.add_data', VehicleID=VehicleID))
    SNo = S[0]

    SID = session.get('incrementedSNo')
    print('Final render_template k upar')
    
    return render_template('add/bookingslot.html', SNo = S[0],VehicleID=VehicleID, BSlotID=BSlotID)

@booking.route('/booking/customSlot', methods = ['GET', 'POST'])
@login_required
def customSlot(): 
    print('customslot ke andar')
    VehicleID = session.get('VehicleID')
    print('session wali vehicleid', VehicleID)
    # VehicleID = request.args.get('VehicleID')
    # session['VehicleID'] = VehicleID
    print('vacantslots k upar')
    VacantSlots = '''
        SELECT b.BSlotID FROM bookingslot b 
        WHERE b.TimeFrom = "00:00:00" and b.TimeTo = "00:00:00" and b.duration= '';
    '''
    cursor.execute(VacantSlots)
    db.commit()
    availableSlots = cursor.fetchall()
    print('available slots: ', availableSlots)
    slots = [slot[0] for slot in availableSlots]
    print('slots: ', slots)
    print('vacantslots k niche')
    if not VehicleID:
        print('if not vehicleID mai gaya')
        flash('An error occurred. Please try again later', 'error')
        # return redirect(url_for('bookingslot.customSlot', VehicleID=VehicleID, BSlotID=BSlotID))
    cursor.execute('SELECT SNo FROM vehicle WHERE VehicleID=%s', (VehicleID,))
    db.commit()
    SNo = cursor.fetchone()
    S_No = SNo[0]
    print('get mai sabse niche post k bahar')
    if request.method == 'POST':
        print('post mai gaya')
        BSlotID = request.form.get('BSlotID')
        Date = request.form.get('Date')
        TimeFrom = request.form.get('TimeFrom')
        duration = request.form.get('duration')

        if not Date:
            print('if not date')
            flash('An error occurred. Please try again later', 'error')
            return redirect(url_for('bookingslot.customSlot', VehicleID=VehicleID, BSlotID=BSlotID))

        if not TimeFrom:
            flash('An error occurred. Please try again later', 'error')
            return redirect(url_for('bookingslot.customSlot', VehicleID=VehicleID, BSlotID=BSlotID))

        if not duration:
            print('if not duration')
            flash('An error occurred. Please try again later', 'error')
            return redirect(url_for('bookingslot.customSlot', VehicleID=VehicleID, BSlotID=BSlotID))

        if not SNo:
            print('if not SNo')
            flash('An error occurred. Please try again later','error')
            return  redirect(url_for('bookingslot.customSlot', VehicleID=VehicleID, SNo=SNo))

        if not BSlotID:
            print('if not BSlotID')
            flash('Error fetching your BSlotID','error')
            return redirect(url_for('bookingslot.customSlot',VehicleID=VehicleID, SNo=SNo)) 
        print('sare if not k niche')
        
        try:
            print('durationstr wale try mai')
            durationStr = int(duration)

        except ValueError as ve:
            print('durationstr wale except mai')
            flash('duration must be a valid number', 'error')
            return redirect(url_for('bookingslot.customSlot', VehicleID=VehicleID, SNo=SNo))
        
        TimeFormat = '%H:%M'
        timeFrom_dt = datetime.strptime(TimeFrom, TimeFormat)
        timeTo_dt = timeFrom_dt + timedelta(hours=durationStr)
        TimeTo = timeTo_dt.strftime(TimeFormat)
        print(f"VehicleID: {VehicleID}, Date: {Date}, TimeFrom: {TimeFrom}, duration: {duration}, TimeTo: {TimeTo}, SNo: {S_No}")

        try:
            print('update query wale try k andar')
            update_query = '''
                UPDATE bookingslot
                SET date=%s, duration=%s, TimeFrom=%s, TimeTo=%s, SNo=%s, VehicleID=%s
                WHERE BSlotID=%s
            '''
            cursor.execute(update_query, (Date,  duration, TimeFrom, TimeTo, S_No, VehicleID,BSlotID))
            db.commit()
            data = cursor.fetchone()
            return redirect(url_for('payment.add_data', VehicleID=VehicleID, SNo=S_No))
        except  mysql.connector.Error as e:
            print('update query wale except k andar')
            print(e)
            db.rollback()
            flash('Error adding data')
            # return render_template('add/bookingslot.html')
            return redirect(url_for('bookingslot.customSlot', VehicleID=VehicleID))

        return redirect(url_for('payment.add_data', VehicleID=VehicleID,SNo=S_No))
    BSlotID = session.get('BSlotID')
    cursor.execute("SELECT SNo FROM vehicle WHERE VehicleID=%s", (VehicleID,))
    S = cursor.fetchone()
    db.commit()
    if S == None:
        # flash('An error occured. Please try again later.', 'error')
        return redirect(url_for('bookingslot.customSlot', VehicleID=VehicleID))
    SNo = S[0]

    print('Final render_template k upar')
    return render_template('add/CustomVehicle.html', SNo = S[0], slots=slots, VehicleID=VehicleID)


@booking.route('/booking/another_slot')
@login_required
def anotherSlot():
    VehicleID = session.get('VehicleID')
    print('VehicleID: ', VehicleID)
    try:
        fetchID = '''SELECT BSlotID FROM bookingslot WHERE TimeFrom="00:00:00" and TimeTo="00:00:00" and duration='' '''
        cursor.execute(fetchID)
        db.commit()
        BSlotID = cursor.fetchone()[0]
    except mysql.connector.Error as e:
        db.rollback()
        print(e)
        flash('BSlotID is not defined', 'error')
        return redirect(url_for('bookingslot.anotherSlot', VehicleID=VehicleID))

    cursor.execute('SELECT SNo FROM vehicle WHERE VehicleID=%s', (VehicleID,))
    db.commit()
    SNo = cursor.fetchone()
    if not SNo:
        flash('An error occurred. Please try again', 'error')
        return redirect(url_for('bookingslot.anotherSlot', VehicleID=VehicleID))
    S_No = SNo[0]

    if request.method == 'POST':
        VehicleID = request.form.get('VehicleID')
        BSlotID = request.form.get('BSlotID')
        TimeFrom = request.form.get('TimeFrom')
        duration = request.form.get('duration')

        TimeFormat = '%H:%M'
        timeFrom_dt = datetime.strptime(TimeFrom, TimeFormat)
        timeTo_dt = timeFrom_dt + timedelta(hours=durationStr)
        TimeTo = timeTo_dt.strftime(TimeFormat)

        try:
            durationStr = int(duration)

        except ValueError as ve:
            flash('duration must be a valid number', 'error')
            return redirect(url_for('bookingslot.customSlot', VehicleID=VehicleID, SNo=SNo))

        if not VehicleID:
            flash('An error occurred. Please try again.','error')
            return redirect(url_for('bookingslot.anotherSlot', VehicleID=VehicleID))

        if not BSlotID:
            flash('An error occurred. Please try again.','error')
            return redirect(url_for('bookingslot.anotherSlot', VehicleID=VehicleID))

        if not TimeFrom:
            flash('An error occurred. Please try again.', 'error')
            return  redirect(url_for('bookingslot.anotherSlot', VehicleID=VehicleID))

        if not duration:
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('bookingslot.anotherSlot'))
        
        try:
            update_query = '''
                UPDATE bookingslot
                SET date=%s, duration=%s, TimeFrom=%s, TimeTo=%s, SNo=%s, VehicleID=%s
                WHERE BSlotID=%s
            '''
            cursor.execute(update_query, (Date,  duration, TimeFrom, TimeTo, S_No, VehicleID,BSlotID))
            db.commit()
            data = cursor.fetchone()
            return redirect(url_for('payment.add_data', VehicleID=VehicleID, SNo=S_No))
        except  mysql.connector.Error as e:
            print(e)
            db.rollback()
            flash('Error adding data')
            # return render_template('add/bookingslot.html')
            return redirect(url_for('bookingslot.customSlot', VehicleID=VehicleID))
        return redirect(url_for('payment.add_data', VehicleID=VehicleID,SNo=S_No))
    BSlotID = session.get('BSlotID')
    cursor.execute("SELECT SNo FROM vehicle WHERE VehicleID=%s", (VehicleID,))
    S = cursor.fetchone()
    db.commit()
    if S == None:
        # flash('An error occured. Please try again later.', 'error')
        return redirect(url_for('bookingslot.anotherSlot', VehicleID=VehicleID))
    SNo = S[0]

    print('Final render_template k upar')
    return render_template('add/anotherSlot.html', SNo = S[0], slots=slots)



@booking.route('/bookingslot/add/<int:BSlotID>')
@login_required
def payment(BSlotID):
    return render_template('add/owner.html', VehicleID=VehicleID, SNo=SNo)

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

