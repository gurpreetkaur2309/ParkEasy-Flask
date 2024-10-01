import re
from flask import redirect, render_template, session, url_for, Blueprint, flash, request
from datetime import date, datetime, timedelta
import bookingslot
from db import db, cursor
import mysql.connector
from auth import login_required
from utils import requires_role
from flask_paginate import Pagination
from utils import requires_role
import csv
Vehicle = Blueprint('vehicle', __name__)


@Vehicle.route('/vehicle')
@login_required
@requires_role('admin')
def display():
    page = request.args.get('page', type=int, default=1)
    per_page = 20
    if page < 1:
        flash('Page does not exist')
        return redirect(url_for('vehicle.display', page=1))

    offset = (page - 1) * per_page
    update_query = '''
        UPDATE vehicle v
        JOIN bookingslot b ON v.VehicleID = b.BSlotID
        SET v.VehicleType = ' ', v.VehicleNumber=' '
        WHERE b.TimeFrom is '' and b.TimeTo is ''
    '''
    try:
        cursor.execute(update_query)
        db.commit()
    except mysql.connector.Error as e:
        db.rollback()
        flash('Error updating data to null', 'danger')

    cursor.execute('SELECT VehicleID, VehicleType, VehicleNumber FROM vehicle limit %s offset %s;', (per_page, offset))
    data = cursor.fetchall()
    db.commit()

    Null_query = '''
        SELECT v.VehicleID 
        FROM vehicle v
        JOIN bookingslot b on v.VehicleID = b.BSlotID
        WHERE b.TimeFrom = ' ' and b.TimeTo = ' ' 
    '''
    cursor.execute(Null_query)
    db.commit()
    NullID = cursor.fetchone()

    has_next = len(data) == per_page
    pagination = Pagination(page=page, per_page=per_page)

    return render_template('view/vehicle.html', data=data, pagination=pagination, has_next=has_next, page=page,
                           per_page=per_page, NullID=NullID)

def ValidNumber(VehicleNumber):
    pattern = r"^[A-Z]{2}[ -]?\d{2}[ -]?[A-Z]{1,2}[ -]?\d{1,4}$"
    return re.search(pattern, VehicleNumber)

@Vehicle.route('/vehicle/add', methods=['POST', 'GET'])
@login_required
def add_data():
    data = []
    print('vehicle wale add data mai gaya')
    print('inside add_data function')
    username = session.get('username')
    print('username: ', username)
    try:
        print('sNo fetch wale try mai gaya')
        SNo = 'SELECT SNo FROM user WHERE username=%s'
        cursor.execute(SNo,(username,))
        db.commit()
        SNo = cursor.fetchone()
        S_No = SNo[0]
        print('SNo: ', S_No)

    except mysql.connector.Error as e:
        print('sNo fetch wale except mai gaya')
        print(e)
        db.rollback()
        flash('An error occurred. Please try again later','error')
        # return redirect(url_for('vehicle.add_data', SNo=SNo))
    try:
        print('VID fetch wale try mai gaya')
        VID = 'SELECT max(VehicleID)+1 as VID FROM Vehicle'
        cursor.execute(VID)
        maxVID = cursor.fetchone()[0]
        print('maxVID', maxVID)
        db.commit()
    except mysql.connector.Error as e:
        print('VID fetch wale try except gaya')
        print(e)
        db.rollback()
        flash('An error occured. Please try again','error')
        return redirect(url_for('vehicle.add_data', SNo = S_No))
    print('get method k andar sare try except k bahar')
    VehicleID = maxVID

    if request.method == 'POST':
        if request.files:
            uploaded_file = request.files['filename']
            filepath = os.path.join(app.config['FILE_UPLOADS'], uploaded_file.filename)
            uploaded_file.save(filepath)
            with open(filepath) as file:
                csv_file = csv.reader(file)
                for row in csv_file:
                    data.append(row)
            return redirect(request.url)

        print('post method mai gaya')
        print('post methd ke niche', S_No)
        if not username: 
            print('username not found')
            flash('No username','error')
            return redirect(url_for('vehicle.add_data'))

        print('VehicleID', VehicleID)
        print('Vehicle ID k niche', S_No)
        if not VID:
            flash('Cannot continue without vehicleID', 'danger')
            return redirect(url_for('vehicle.add_data', SNo=S_No))  
        session['VehicleID'] = VehicleID
        print(session['VehicleID'], 'session wali vehicleid')
        VehicleType = request.form.get('VehicleType')
        VehicleNumber = request.form.get('VehicleNumber')
        VehicleName = request.form.get('VehicleName')
        # fetch_SNo = ''' 
        #         SELECT u.SNo FROM user u 
        #         JOIN vehicle v on u.SNo = v.SNo
        #     '''
        # cursor.execute(fetch_SNo, (VehicleID,SNo))
        # SNo = cursor.fetchone()
        # print(SNo,'sno')
        # S_No = SNo[0] if SNo else None  

        check_number_query = 'SELECT VehicleNumber FROM vehicle'
        print('check query k niche', S_No)
        cursor.execute(check_number_query)
        db.commit()
        existing_number = cursor.fetchall()
        print(existing_number, 'existing number')
        
        if existing_number == VehicleNumber:
            flash(f'A vehicle with this Registration number has already booked slot','error')
            return redirect(url_for('vehicle.add_data', SNo=S_No))
        
        if not S_No:
            print('not s no.')
            flash('An error occurred. Please try again after sometime', 'error')
            return redirect(url_for('vehicle.add_data', SNo=S_No))  
        
        if not ValidNumber(VehicleNumber):
            flash('Registration Number is not valid')
            return redirect(url_for('vehicle.add_data', SNo=S_No))  
        print('if not validnumber k niche', S_No)
        try:
            print('insert query wale try mai', S_No)
            insert_query = '''
                INSERT INTO vehicle (VehicleID, VehicleType, VehicleNumber, VehicleName, SNo) VALUES (%s, %s, %s, %s, %s) 
            '''
            cursor.execute(insert_query, (VehicleID, VehicleType, VehicleNumber, VehicleName, S_No,))
            db.commit()
            print('')
        except mysql.connector.Error as e:
            print('insert query wale except k andar',S_No)
            print('The error is',e)
            db.rollback()
            flash('Error adding data', 'error')
            return redirect(url_for('vehicle.add_data', SNo=S_No)) 
        print(data, 'cars')

        print('sabse niche return redirect wale k upar', S_No)
        return redirect(url_for('bookingslot.add_data', VehicleID=VehicleID, S_No=S_No))

    return render_template('add/vehicle.html', SNo=S_No, data=data)

@Vehicle.route('/vehicle/admin/add', methods=['GET','POST'])
@login_required
@requires_role('admin')
def AdminVehicle():
    if request.method == 'POST':
        VehicleID = request.form['VehicleID']
        VehicleType = request.form['VehicleType']
        VehicleNumber = request.form['VehicleNumber']
        name = request.form['name']
        address = request.form['address']
        contact = request.form['contact']
        date = request.form['date']
        TimeFrom = request.form['TimeFrom']
        duration = request.form['duration']
        mode = request.form['mode']
            
        try:
            durationStr = int(duration)
        except ValueError as ve:
            flash('duration must be a valid number', 'error')
            return redirect(url_for('bookingslot.AdminVehicle'))

        if not VehicleID:
            flash('An issue occurred. Please try after sometime','error')
            print('VehicleID not found')
            return redirect(url_for('vehicle.AdminVehicle'))

        if not VehicleType:
            flash('An issue occurred. Please try after sometime','error')
            print('VehicleType not found')
            return redirect(url_for('vehicle.AdminVehicle'))

        if not VehicleNumber:
            flash('An issue occurred. Please try after sometime','error')
            print('VehicleNumber not found')
            return redirect(url_for('vehicle.AdminVehicle'))

        if not name:
            flash('An issue occurred. Please try after sometime','error')
            print('name not found')
            return redirect(url_for('vehicle.AdminVehicle'))
        
        if not address:
            flash('An issue occurred. Please try after sometime','error')
            print('owner address not found')
            return redirect(url_for('vehicle.AdminVehicle'))
        
        if not contact:
            flash('An issue occurred. Please try after sometime','error')
            print('contact not found')
            return redirect(url_for('vehicle.AdminVehicle'))

        if not date:
            flash('An issue occurred. Please try after sometime','error')
            print('date details not found')
            return redirect(url_for('vehicle.AdminVehicle'))

        if not TimeFrom:
            flash('An issue occurred. Please try after sometime','error')
            print('TimeFrom details not found')
            return redirect(url_for('vehicle.AdminVehicle'))

        if not duration:
            flash('An issue occurred. Please try after sometime','error')
            print('duration details not found')
            return redirect(url_for('vehicle.AdminVehicle'))
        print('rate=0 ke upar')
        rate = 0 
        print('total price wali condition ke upar')
        if VehicleType == 'car':
            print('car ke andar')
            rate = 13
        if VehicleType == '2-Wheeler':
            print('2 wheeler k andar')
            rate = 8
        if VehicleType == 'Heavy-Vehicle':
            print('heavy vehicle k andar')
            rate = 15
        if VehicleType == 'Luxury-Vehicle':
            print('luxury vehicle k andar')
            rate = 18
        print('Totalprice k upar condition k bahar')
        TotalPrice = rate * durationStr
        print('TotalPrice', TotalPrice)

        if not mode:
            flash('An issue occurred. Please try again after sometime','error')
            print('Mode not found')
            return redirect(url_for('vehicle.AdminVehicle'))

        if not TotalPrice:
            flash('An issue occurred. Please try again after sometime','error')
            print('TotalPrice not found')
            return redirect(url_for('vehicle.AdminVehicle'))

        print(VehicleID)
        cursor.execute('SELECT SNO FROM Vehicle WHERE VehicleID=VehicleID')
        db.commit()
        S_No = cursor.fetchone()
        SNo = S_No[0]
        print(SNo, ': SNo')
        if not S_No:
            return "Server Error"
        if not SNo:
            return "Server Error"

        add_query = '''
            UPDATE admin a set SNo = SNo 
        '''
        cursor.execute(add_query)
        db.commit()

        TimeFormat = '%H:%M'
        timeFrom_dt = datetime.strptime(TimeFrom, TimeFormat)
        timeTo_dt = timeFrom_dt + timedelta(hours=durationStr)
        TimeTo = timeTo_dt.strftime(TimeFormat)

        try:
            update_query = '''
            UPDATE vehicle v 
            INNER JOIN bookingslot b ON v.VehicleID = b.BSlotID
            INNER JOIN payment p ON v.VehicleID = p.PaymentID
            INNER JOIN admin a ON a.SNo = v.SNo
            SET v.VehicleType=%s, v.VehicleNumber=%s,
                b.date=%s, b.TimeFrom=%s, b.TimeTo=%s, b.duration=%s,
                p.mode=%s, p.TotalPrice=%s
            WHERE VehicleID=%s
            '''
            cursor.execute(update_query, (VehicleType, VehicleNumber, date, TimeFrom, TimeTo, duration, mode, TotalPrice, VehicleID))
            db.commit()
            print('update query',update_query)
        except mysql.connector.Error as e:
            flash('An error occurred. Please try after sometime','error')
            print('update query issue: ', e)
            db.rollback()
            return redirect(url_for('vehicle.AdminVehicle'))
        
        try:
            print('insert wale try ke andar')
            print(SNo,'Sno')
            insert_query = '''
                INSERT INTO owner(name, address, contact) values (%s, %s, %s)
            '''
            cursor.execute(insert_query, (name,address,contact,))
            db.commit()
        except mysql.connector.Error as e:
            print(e, 'is the error')
            flash('An error occurred. Please try again later','error')
            return redirect(url_for('vehicle.AdminVehicle'))
        PaymentID = VehicleID
        return redirect(url_for('payment.Generate_Receipt', PaymentID=PaymentID,duration=duration, TotalPrice=TotalPrice))

    cursor.execute("SELECT VehicleID,SNo FROM vehicle WHERE VehicleType='' and VehicleNumber='' ")
    db.commit()
    availableSlots = cursor.fetchall()
    VID = [slot[0] for slot in availableSlots]
    print(VID, 'VID')
    if not availableSlots:
        flash('No slots are available currently. Please try again later','error')
        return redirect(url_for('auth.dashboard'))
        try:
            print('fetch query wale try ke andar')
            fetch_query = '''
                SELECT v.VehicleID, v.VehicleType, v.VehicleNumber, 
                       b.Date, b.TimeFrom, b.TimeTo, b.duration, 
                       a.SNo, a.username,     
                       o.name, o.contact,     
                       p.TotalPrice, p.mode 
                       FROM vehicle v
                       JOIN bookingslot b ON v.VehicleID = b.BSlotID 
                       JOIN admin a ON v.SNo = a.SNo 
                       JOIN owner o ON v.SNo = o.SNo 
                       JOIN payment p ON b.BSlotID = p.PaymentID 
                       ORDER BY  b.Date DESC, 
                       b.TimeFrom DESC LIMIT 1
            '''
            cursor.execute(fetch_query)
            data = cursor.fetchone()
            print('admin data', data)
            if data is None:
                print('No data')
                flash('No data found', 'error')
                return redirect(url_for('vehicle.AdminVehicle'))

            VehicleID = data[0]
            VehicleType = data[1]
            VehicleNumber = data[2]
            date = data[3]
            TimeFrom = data[4]
            TimeTo = data[5]
            duration = data[6]
            SNo = data[7]
            username = data[8]
            name = data[9]
            contact = data[10]
            TotalPrice = data[11]
            mode = data[12]
            
            cursor.execute("SELECT SNo FROM vehicle WHERE VehicleID=%s")
            db.commit()
            SNo = cursor.fetchone()
            S_No = SNo[0]
        except mysql.connector.Error as e:
            print('fetch query wale except ke andar')
            print(e)
            flash('Error processing your payment', 'error')
            db.rollback()
            return redirect(url_for('auth.MyBookings'))

        try:
            print('insert query wale try ke andar')
            insert_query = '''
                INSERT INTO allotment(VehicleID, SNo, username, date, TimeFrom, TimeTo, duration, name, contact, TotalPrice, mode, VehicleType, VehicleNumber) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)                '''
            # cursor.execute(insert_query, (VehicleID, username, date, TimeFrom, TimeTo, Duration, name, contact, TotalPrice, mode, VehicleType, VehicleNumber))
            cursor.execute(insert_query, (VehicleID, S_No, username, date, TimeFrom, TimeTo, Duration, name, contact, TotalPrice, mode, VehicleType, VehicleNumber))
            db.commit()

            if(TotalPrice==0):
                db.rollback()
                return "Server error" 
                
        except mysql.connector.Error as e:
            print('insert query wale allotment ke andar')
            print(e)
            flash('Error adding allotment', 'error')
            return redirect(url_for('vehicle.AdminVehicle'))

        return redirect(url_for('payment.Generate_Receipt',duration=duration, TotalPrice=TotalPrice, mode=mode, PaymentID=PaymentID))

    return render_template('add/adminVehicleSlot.html', VID=VID)


@Vehicle.route('/user/vehicles', methods=['GET','POST'])
@login_required
@requires_role('user')
def ChooseVehicle():
    print('ChooseVehicle function mai gaya')
    username = session.get('username')
    print('username in choosevehicle', username)
    print('get method chal rahi hai')
    VehicleID = session.get('VehicleID')
    try:

        fetchSNo = '''
            SELECT v.SNo FROM vehicle v
            INNER JOIN user u ON u.SNo = v.SNo
            WHERE u.username=%s
            '''
        cursor.execute(fetchSNo, (username,))
        db.commit()
        VehicleSNo = cursor.fetchone()
        if VehicleSNo is None:
            flash('No vehicles found. Please add a vehicle', 'success')
            return redirect(url_for('vehicle.add_data'))

        print('VehicleSNo', VehicleSNo)
        SNo = VehicleSNo[0]
        print('SNo',SNo)
   
    except mysql.connector.Error as e:
        print(e)
        db.rollback()
        flash('Server returns null response. Please try again later', 'error')
        return redirect(url_for('vehicle.add_data'))
    try:
        print('fetch query wale try mau')
        fetch_query = 'SELECT * FROM vehicle v INNER JOIN user u on u.SNo=v.SNo WHERE u.SNo=%s AND u.username=%s'
        cursor.execute(fetch_query, (SNo, username,))
        db.commit()
        vehicles = cursor.fetchall()
        vehicleList = [[vehicle[0], vehicle[1], vehicle[2], vehicle[3], vehicle[4]] for vehicle in vehicles]

    except mysql.connector.Error as e:
        print('fetch query wale except mai gaya')
        print(e)
        db.rollback()
        flash('Server returned a null response. Please try again later','error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        print('post method k andar')
        print('selectedid k upar')
        SelectedID = request.form.get('VehicleID')
        print('request.form selectedid k niche')
        print('selectedID: ', SelectedID)

        if SelectedID:
            print('if selectedid k andar')
            flash('Vehicle selected successfully','success')
            return redirect(url_for('bookingslot.add_data', VehicleID=SelectedID, SNo=SNo))
        else:
            print('else selectedid mai gaya')
            flash('please select a vehicle to continue','error')
            return redirect(url_for('vehicle.ChooseVehicle'))


        if not vehicleList:
            print('if not vehicleList mai gaya')
            print('No vehicles found.')
            flash('No vehicles found. Please add a vehicle', 'error')
            return redirect(url_for('vehicle.add_data', SNo=SNo))
        # return redirect(url_for('vehicle.ChooseVehicle', SNo=SNo, VehicleType=VehicleType, VehicleNumber=VehicleNumber, VehicleName=VehicleName))
        return render_template('view/ChooseVehicle.html', VehicleType=VehicleType, VehicleNumber=VehicleNumber, VehicleName=VehicleName)
    if not vehicleList:
        print('else mai gaya')

        flash('No vehicles found. Please add a vehicle ', 'error')
        return redirect(url_for('vehicle.add_data', SNo=SNo))
    return render_template('view/ChooseVehicle.html', vehicles = vehicleList)


@Vehicle.route('/vehicle/bookingslot/add/<int:VehicleID>', methods=['GET', 'POST'])
@login_required
def bookingslot(VehicleID):
    return render_template('add/bookingslot.html', VehicleID=VehicleID, SNo=SNo)

@Vehicle.route('/vehicle/edit/<int:VehicleID>', methods=['GET', 'POST'])
@login_required
def edit_data(VehicleID):
    if request.method == 'POST':
        VehicleType = request.form['VehicleType']
        VehicleNumber = request.form['VehicleNumber']
        try:
            update_query = '''Update vehicle
            set VehicleType=%s, VehicleNumber=%s
            where VehicleID=%s
            '''
            cursor.execute(update_query, (VehicleType, VehicleNumber, VehicleID))
            db.commit()
            flash('Data updated successfully')
            return redirect(url_for('vehicle.display'))
        except mysql.connector.Error as e:
            db.rollback()
            flash('Error updating data')
    fetch_query = 'Select VehicleID, VehicleType, VehicleNumber from vehicle where VehicleID=%s'
    cursor.execute(fetch_query, (VehicleID,))
    db.commit()
    data = cursor.fetchone()
    if data is None:
        flash('No data found')
        return redirect(url_for('vehicle.display'))
    return render_template('edit/vehicle.html', data=data)


@Vehicle.route('/vehicle/delete/<int:VehicleID>', methods=['GET', 'POST'])
@login_required
def delete_data(VehicleID):
    if request.method == 'POST':
        try:
            delete_query = '''DELETE FROM vehicle WHERE VehicleID=%s'''
            cursor.execute(delete_query, (VehicleID,))
            flash('Data deleted successfully')
            return redirect(url_for('vehicle.display'))
        except mysql.connector.Error as e:
            db.rollback()
            flash('Error deleting data')
    fetch_query = "SELECT VehicleID, VehicleType, VehicleNumber FROM vehicle WHERE VehicleID=%s"
    cursor.execute(fetch_query, (VehicleID,))
    data = cursor.fetchone()
    if data is None:
        flash('Data not found')
        return redirect(url_for('vehicle.display'))
    return render_template('delete/vehicle.html', data=data)    
