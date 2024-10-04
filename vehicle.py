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
    with open("static/DataSet.csv") as f:
        lines = list(csv.reader(f))
    first_elements = [row[0] for row in lines if row]
    data = []
    username = session.get('username')
    try:
        SNo = 'SELECT SNo FROM user WHERE username=%s'
        cursor.execute(SNo,(username,))
        db.commit()
        SNo = cursor.fetchone()
        S_No = SNo[0]

    except mysql.connector.Error as e:
        print(e)
        db.rollback()
        flash('An error occurred. Please try again later','error')
        # return redirect(url_for('vehicle.add_data', SNo=SNo))
    try:
        VID = 'SELECT max(VehicleID)+1 as VID FROM Vehicle'
        cursor.execute(VID)
        maxVID = cursor.fetchone()[0]
        db.commit()
    except mysql.connector.Error as e:
        print(e)
        db.rollback()
        flash('An error occured. Please try again','error')
        return redirect(url_for('vehicle.add_data', SNo = S_No))
    VehicleID = maxVID

    if request.method == 'POST':
        if not username: 
            print('username not found')
            flash('No username','error')
            return redirect(url_for('vehicle.add_data'))

        if not VID:
            flash('Cannot continue without vehicleID', 'danger')
            return redirect(url_for('vehicle.add_data', SNo=S_No))  
        session['VehicleID'] = VehicleID

        VehicleType = request.form.get('VehicleType')
        VehicleNumber = request.form.get('VehicleNumber')
        VehicleName = request.form.get('VehicleName') 

        check_number_query = 'SELECT VehicleNumber FROM vehicle'
        cursor.execute(check_number_query)
        db.commit()
        existing_number = cursor.fetchall()
        
        if VehicleNumber in existing_number:
            flash(f'This vehicle is already saved. Please select this vehicle','error')
            return redirect(url_for('vehicle.ChooseVehicle'))
        
        if not S_No:
            flash('An error occurred. Please try again after sometime', 'error')
            return redirect(url_for('vehicle.add_data', SNo=S_No))  
        
        if not ValidNumber(VehicleNumber):
            flash('Registration Number is not valid')
            return redirect(url_for('vehicle.add_data', SNo=S_No))  
        try:
            insert_query = '''
                INSERT INTO vehicle (VehicleID, VehicleType, VehicleNumber, VehicleName, SNo) VALUES (%s, %s, %s, %s, %s) 
            '''
            cursor.execute(insert_query, (VehicleID, VehicleType, VehicleNumber, VehicleName, S_No,))
            db.commit()
            print('')
        except mysql.connector.Error as e:
            db.rollback()
            flash('Error adding data', 'error')
            return redirect(url_for('vehicle.add_data', SNo=S_No)) 

        return redirect(url_for('bookingslot.add_data', VehicleID=VehicleID, S_No=S_No))

    return render_template('add/vehicle.html', SNo=S_No, data=data, first_elements=first_elements)

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
            return redirect(url_for('vehicle.AdminVehicle'))

        if not VehicleType:
            flash('An issue occurred. Please try after sometime','error')
            return redirect(url_for('vehicle.AdminVehicle'))

        if not VehicleNumber:
            flash('An issue occurred. Please try after sometime','error')
            return redirect(url_for('vehicle.AdminVehicle'))

        if not name:
            flash('An issue occurred. Please try after sometime','error')
            return redirect(url_for('vehicle.AdminVehicle'))
        
        if not address:
            flash('An issue occurred. Please try after sometime','error')
            return redirect(url_for('vehicle.AdminVehicle'))
        
        if not contact:
            flash('An issue occurred. Please try after sometime','error')
            return redirect(url_for('vehicle.AdminVehicle'))

        if not date:
            flash('An issue occurred. Please try after sometime','error')
            return redirect(url_for('vehicle.AdminVehicle'))

        if not TimeFrom:
            flash('An issue occurred. Please try after sometime','error')
            return redirect(url_for('vehicle.AdminVehicle'))

        if not duration:
            flash('An issue occurred. Please try after sometime','error')
            return redirect(url_for('vehicle.AdminVehicle'))
        
        rate = 0 
        if VehicleType == 'car':
            rate = 13

        if VehicleType == '2-Wheeler':
            rate = 8

        if VehicleType == 'Heavy-Vehicle':
            rate = 15

        if VehicleType == 'Luxury-Vehicle':
            rate = 18

        TotalPrice = rate * durationStr

        if not mode:
            flash('An issue occurred. Please try again after sometime','error')
            return redirect(url_for('vehicle.AdminVehicle'))

        if not TotalPrice:
            flash('An issue occurred. Please try again after sometime','error')
            return redirect(url_for('vehicle.AdminVehicle'))

        print(VehicleID)
        cursor.execute('SELECT SNO FROM Vehicle WHERE VehicleID=VehicleID')
        db.commit()
        S_No = cursor.fetchone()
        SNo = S_No[0]

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
        except mysql.connector.Error as e:
            flash('An error occurred. Please try after sometime','error')
            db.rollback()
            return redirect(url_for('vehicle.AdminVehicle'))
        
        try:
            insert_query = '''
                INSERT INTO owner(name, address, contact) values (%s, %s, %s)
            '''
            cursor.execute(insert_query, (name,address,contact,))
            db.commit()
        except mysql.connector.Error as e:
            flash('An error occurred. Please try again later','error')
            return redirect(url_for('vehicle.AdminVehicle'))
        PaymentID = VehicleID
        return redirect(url_for('payment.Generate_Receipt', PaymentID=PaymentID,duration=duration, TotalPrice=TotalPrice))

    cursor.execute("SELECT VehicleID,SNo FROM vehicle WHERE VehicleType='' and VehicleNumber='' ")
    db.commit()
    availableSlots = cursor.fetchall()
    VID = [slot[0] for slot in availableSlots]
    if not availableSlots:
        flash('No slots are available currently. Please try again later','error')
        return redirect(url_for('auth.dashboard'))
        try:
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
            if data is None:
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
            print(e)
            flash('Error processing your payment', 'error')
            db.rollback()
            return redirect(url_for('auth.MyBookings'))

        try:
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
            print(e)
            flash('Error adding allotment', 'error')
            return redirect(url_for('vehicle.AdminVehicle'))

        return redirect(url_for('payment.Generate_Receipt',duration=duration, TotalPrice=TotalPrice, mode=mode, PaymentID=PaymentID))

    return render_template('add/adminVehicleSlot.html', VID=VID)


@Vehicle.route('/user/vehicles', methods=['GET','POST'])
@login_required
@requires_role('user')
def ChooseVehicle():
    username = session.get('username')
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

        SNo = VehicleSNo[0]
   
    except mysql.connector.Error as e:
        print(e)
        db.rollback()
        flash('Server returns null response. Please try again later', 'error')
        return redirect(url_for('vehicle.add_data'))
    try:
        fetch_query = 'SELECT * FROM vehicle v INNER JOIN user u on u.SNo=v.SNo WHERE u.SNo=%s AND u.username=%s'
        cursor.execute(fetch_query, (SNo, username,))
        db.commit()
        vehicles = cursor.fetchall()
        vehicleList = [[vehicle[0], vehicle[1], vehicle[2], vehicle[3], vehicle[4]] for vehicle in vehicles]

    except mysql.connector.Error as e:
        print(e)
        db.rollback()
        flash('Server returned a null response. Please try again later','error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        SelectedID = request.form.get('VehicleID')

        if SelectedID:
            flash('Vehicle selected successfully','success')
            return redirect(url_for('bookingslot.add_data', VehicleID=SelectedID, SNo=SNo))
        else:
            flash('please select a vehicle to continue','error')
            return redirect(url_for('vehicle.ChooseVehicle'))


        if not vehicleList:
            flash('No vehicles found. Please add a vehicle', 'error')
            return redirect(url_for('vehicle.add_data', SNo=SNo))
        # return redirect(url_for('vehicle.ChooseVehicle', SNo=SNo, VehicleType=VehicleType, VehicleNumber=VehicleNumber, VehicleName=VehicleName))
        return render_template('view/ChooseVehicle.html', VehicleType=VehicleType, VehicleNumber=VehicleNumber, VehicleName=VehicleName)
    
    if not vehicleList:
        flash('No vehicles found. Please add a vehicle ', 'error')
        return redirect(url_for('vehicle.add_data', SNo=SNo))
    return render_template('view/ChooseVehicle.html', vehicles = vehicleList)


@Vehicle.route('/vehicle/bookingslot/add/<int:VehicleID>', methods=['GET', 'POST'])
@login_required
def bookingslot(VehicleID):
    return render_template('add/bookingslot.html', VehicleID=VehicleID, SNo=SNo)

@Vehicle.route('/user/vehicle/edit/<int:VehicleID>', methods=['GET','POST'])
@login_required
def edit_vehicle(VehicleID):
    if request.method == 'POST':
        VehicleType = request.form['VehicleType']
        VehicleNumber = request.form['VehicleNumber']
        VehicleName = request.form['VehicleName']
        try:
            update_query = '''
                UPDATE vehicle
                SET VehicleType=%s, VehicleNumber=%s, VehicleName=%s 
                WHERE VehicleID=%s
            '''
            cursor.execute(update_query, (VehicleType, VehicleNumber, VehicleName, VehicleID))
            db.commit()
            flash('Data updated successfully', 'success')
            return redirect(url_for('vehicle.ChooseVehicle'))
        except mysql.connector.Error as e:
            db.rollback()
            flash('An error occurred. Please try again later', 'error')
            return redirect(url_for('vehicle.ChooseVehicle'))
    fetch_query = 'SELECT VehicleID, VehicleType, VehicleNumber, VehicleName from vehicle where VehicleID=%s'
    cursor.execute(fetch_query, (VehicleID,))
    db.commit()
    data = cursor.fetchone()
    print('data in vehicle is: ', data)
    if data is None:
        flash('No data found')
        return redirect(url_for('vehicle.display'))
    return render_template('edit/ChooseVehicle.html', data=data)

@Vehicle.route('/user/vehicle/Add',methods=['GET','POST'])
@login_required
def add_vehicle():
    with open("static/DataSet.csv") as f:
        lines = list(csv.reader(f))
    first_elements = [row[0] for row in lines if row]
    print('first_elements: ', first_elements)
    data = []
    username = session.get('username')
    try:
        SNo = 'SELECT SNo FROM user WHERE username=%s'
        cursor.execute(SNo,(username,))
        db.commit()
        SNo = cursor.fetchone()
        S_No = SNo[0]

    except mysql.connector.Error as e:
        print(e)
        db.rollback()
        flash('An error occurred. Please try again later','error')
        # return redirect(url_for('vehicle.add_data', SNo=SNo))
    try:
        VID = 'SELECT max(VehicleID)+1 as VID FROM Vehicle'
        cursor.execute(VID)
        maxVID = cursor.fetchone()[0]
        db.commit()
    except mysql.connector.Error as e:
        print(e)
        db.rollback()
        flash('An error occured. Please try again','error')
        return redirect(url_for('vehicle.add_data', SNo = S_No))
    VehicleID = maxVID

    if request.method == 'POST':
        if not username: 
            flash('No username','error')
            return redirect(url_for('vehicle.add_data'))

        if not VID:
            flash('Cannot continue without vehicleID', 'danger')
            return redirect(url_for('vehicle.add_data', SNo=S_No))  
        session['VehicleID'] = VehicleID
        VehicleType = request.form.get('VehicleType')
        VehicleNumber = request.form.get('VehicleNumber')
        VehicleName = request.form.get('VehicleName')
        action = request.form.get('action')
       
        check_number_query = 'SELECT VehicleNumber FROM vehicle'
        cursor.execute(check_number_query)
        db.commit()
        Reg_Number = cursor.fetchall()
        existing_number = [vehicle[0] for vehicle in Reg_Number] 
        
        if VehicleNumber in existing_number:
            flash('This vehicle is already saved. Please select this vehicle','error')
            return redirect(url_for('vehicle.ChooseVehicle'))
        
        if not S_No:
            print('not s no.')
            flash('An error occurred. Please try again after sometime', 'error')
            return redirect(url_for('vehicle.add_data', SNo=S_No))  
        
        if not ValidNumber(VehicleNumber):
            flash('Registration Number is not valid')
            return redirect(url_for('vehicle.add_data', SNo=S_No))  

        try:
            insert_query = '''
                INSERT INTO vehicle (VehicleID, VehicleType, VehicleNumber, VehicleName, SNo) VALUES (%s, %s, %s, %s, %s) 
            '''
            cursor.execute(insert_query, (VehicleID, VehicleType, VehicleNumber, VehicleName, S_No,))
            db.commit()
            print('')
            if action == 'book_slot':
                return redirect(url_for('bookingslot.add_data',VehicleID=VehicleID, SNo=SNo))
            else:
                flash('Vehicle saved successfully')
                return redirect(url_for('auth.dashboard'))
        except mysql.connector.Error as e:
            db.rollback()
            flash('Error adding data', 'error')
            return redirect(url_for('vehicle.add_data', SNo=S_No)) 

    return render_template('add/Save_vehicle.html', SNo=S_No, data=data, first_elements=first_elements)


@Vehicle.route('/vehicle/edit/<int:VehicleID>', methods=['GET', 'POST'])
@login_required
def edit_data(VehicleID):
    if request.method == 'POST':
        VehicleType = request.form['VehicleType']
        VehicleNumber = request.form['VehicleNumber']
        try:
            update_query = '''UPDATE vehicle
            SET VehicleType=%s, VehicleNumber=%s
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

@Vehicle.route('/vehicle/delete/vehicle/<int:VehicleID>', methods=['GET','POST'])
@login_required
def delete_vehicle(VehicleID):
    if request.method == 'POST':
        try:
            delete_query = '''DELETE FROM vehicle WHERE VehicleID=%s'''
            cursor.execute(delete_query, (VehicleID,))
            flash('Data deleted successfully')
            return redirect(url_for('vehicle.ChooseVehicle'))
        except mysql.connector.Error as e:
            db.rollback()
            flash('Error deleting data')
    fetch_query = "SELECT VehicleID, VehicleType, VehicleNumber FROM vehicle WHERE VehicleID=%s"
    cursor.execute(fetch_query, (VehicleID,))
    data = cursor.fetchone()
    if data is None:
        flash('Data not found')
        return redirect(url_for('vehicle.ChooseVehicle'))
    return render_template('delete/ChooseVehicle.html', data=data) 

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
    fetch_query = "SELECT VehicleID, VehicleType, VehicleNumber, VehicleName FROM vehicle WHERE VehicleID=%s"
    cursor.execute(fetch_query, (VehicleID,))
    data = cursor.fetchone()
    print(data,'daya')
    if data is None:
        flash('Data not found')
        return redirect(url_for('vehicle.display'))
    return render_template('delete/vehicle.html', data=data)    
