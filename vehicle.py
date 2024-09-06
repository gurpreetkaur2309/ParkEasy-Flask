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
    print('inside add_data function')
    SNo = request.args.get('SNo')  
    print(SNo, 'sno')
    if request.method == 'POST':
        VehicleID = request.form.get('VehicleID')
        if not VehicleID:
            print('vehicle id ni h')
            flash('Cannot continue without vehicleID', 'danger')
            return redirect(url_for('vehicle.add_data', SNo=SNo))  
        session['VehicleID'] = VehicleID
        VehicleType = request.form.get('VehicleType')
        VehicleNumber = request.form.get('VehicleNumber')
        print(request.form)
        fetch_SNo = ''' 
                SELECT u.SNo FROM user u 
                JOIN vehicle v on u.SNo = v.SNo
            '''
        # cursor.execute(fetch_SNo, (VehicleID,))
        # SNo = cursor.fetchone()
        # print(SNo,'sno')
        S_No = SNo[0] if SNo else None

        
        check_number_query = 'SELECT VehicleNumber FROM vehicle WHERE VehicleID=%s'
        cursor.execute(check_number_query,(VehicleID,))
        db.commit()
        existing_number = cursor.fetchone()
        print(existing_number, 'existing number')
        
        if existing_number and existing_number[0] == VehicleNumber:
            flash(f'A vehicle with this Registration number has already booked slot','error')
            return redirect(url_for('vehicle.add_data', VehicleID=VehicleID, SNo=SNo))
        
        if not S_No:
            print('not s no.')
            flash('An error occurred. Please try again after sometime', 'error')
            return redirect(url_for('vehicle.add_data', SNo=SNo))  
        
        if not ValidNumber(VehicleNumber):
            flash('Registration Number is not valid')
            return redirect(url_for('vehicle.add_data', SNo=SNo))  

        try:
            update_query = '''
                    UPDATE vehicle
                    SET VehicleType=%s, VehicleNumber=%s, SNo=%s
                    WHERE VehicleID=%s
                '''
            cursor.execute(update_query, (VehicleType, VehicleNumber, SNo, VehicleID))
            db.commit()
            #debugging
            cursor.execute('SELECT * from vehicle where vehicleID=%s',(VehicleID,))
            data = cursor.fetchone()
            print('debugging wala data', data)
            ##end

            print('db.commit k niche')
        except mysql.connector.Error as e:
            print('The error is',e)
            db.rollback()
            flash('Error adding data', 'error')
            return redirect(url_for('vehicle.add_data', SNo=SNo)) 

        return redirect(url_for('bookingslot.add_data', VehicleID=VehicleID, SNo=SNo))


    cursor.execute("SELECT VehicleID FROM vehicle WHERE VehicleType = '' and VehicleNumber = '' ")
    availableSlots = cursor.fetchone()
    print(availableSlots, 'available slots')
    VID = availableSlots[0] if availableSlots else None

    if not availableSlots:
        flash('No slots found. Please try after sometime', 'error')
        return redirect(url_for('auth.dashboard'))

    return render_template('add/vehicle.html', VID=VID, SNo=SNo)

@Vehicle.route('/vehicle/bookslot', methods=['GET','POST'])
@login_required
def bookSlot():
    print('inside bookslot function')
    username = session.get('username')
    print('username: ', username)
    fetch_query = 'SELECT SNo FROM user WHERE username=%s'
    cursor.execute(fetch_query, (username,))
    db.commit()
    S_No = cursor.fetchone()
    SNo = S_No[0]
    print(SNo, 'SNo')
 
    if request.method == 'POST':
        VehicleID = request.form['VehicleID']
        if not VehicleID:
            flash('Cannot continue without VehicleID','error')
            return redirect(url_for('vehicle.bookSlot'))
        SNo = session.get('incrementedSNo')
        print(SNo, 'sno inside the post method')
        session['VehicleID'] = VehicleID
        VehicleType = request.form['VehicleType']
        if VehicleType == '0':
            flash('Please select a valid VehicleType','danger')
            return redirect(url_for('vehicle.bookSlot'))
        VehicleNumber = request.form['VehicleNumber']
        if not ValidNumber(VehicleNumber):
            flash('Registration No is not valid')
            return redirect(url_for('vehicle.bookSlot'))

        check_number_query = 'SELECT VehicleNumber FROM vehicle WHERE VehicleID=%s'
        cursor.execute(check_number_query,(VehicleID,))
        db.commit()
        existing_number = cursor.fetchone()
        print(existing_number, 'existing number')
        if existing_number and existing_number[0] == VehicleNumber:
            flash(f'A vehicle with this Registration number has already booked slot','error')
            return redirect(url_for('vehicle.add_data', VehicleID=VehicleID, SNo=SNo))
        
        if not SNo:
            print('not s no.')
            flash('An error occurred. Please try again after sometime', 'error')
            return redirect(url_for('vehicle.add_data', SNo=SNo))  
        
        if not ValidNumber(VehicleNumber):
            flash('Registration Number is not valid')
            return redirect(url_for('vehicle.add_data', SNo=SNo))  

        try:
            update_query = '''
                    UPDATE vehicle
                    SET VehicleType=%s, VehicleNumber=%s, SNo=%s
                    WHERE VehicleID=%s
                '''
            cursor.execute(update_query, (VehicleType, VehicleNumber, S_No, VehicleID))
            db.commit()

            print('db.commit k niche')
        except mysql.connector.Error as e:
            print(e)
            db.rollback()
            flash('Error adding data', 'error')
            return redirect(url_for('vehicle.add_data', SNo=SNo)) 

        return redirect(url_for('bookingslot.bookSlot', VehicleID=VehicleID, SNo=SNo))


    cursor.execute("SELECT VehicleID FROM vehicle WHERE VehicleType = '' and VehicleNumber = '' ")
    availableSlots = cursor.fetchone()
    print(availableSlots, 'available slots')
    VID = availableSlots[0] if availableSlots else None

    if not availableSlots:
        flash('No slots found. Please try after sometime', 'error')
        return redirect(url_for('auth.dashboard'))

    return render_template('add/vehicle.html', VID=VID, SNo=SNo)
        


@Vehicle.route('/vehicle/custom/add', methods=['GET','POST'])
@login_required
def addCustomVehicle():
    if request.method == 'POST':
        print('inside post method')
        VehicleID = request.form['VehicleID']
        print(VehicleID, 'VehicleID')

        session['VehicleID'] = VehicleID
        VehicleType = request.form['VehicleType']
        print(VehicleType, 'VehicleType')
        if VehicleID == 'VehicleID':
            flash('Please select a valid slot number','error')
            return redirect(url_for('vehicle.addCustomVehicle'))

        if VehicleType == '0':
            flash('Please select a valid VehicleType','danger')
            return redirect(url_for('vehicle.addCustomVehicle'))
        VehicleNumber = request.form['VehicleNumber']
        print(VehicleNumber, 'VehicleNumber')
        if not ValidNumber(VehicleNumber):
            flash('Registration Number is not valid')
            return redirect(url_for('vehicle.add_data'))

        if not VehicleID:
            print('VehicleID not found')
            flash('An error occured. Please try again later','error')
            return redirect(url_for('vehicle.addCustomVehicle'))

        if not VehicleType:
            print('VehicleType not found')
            flash('An error occured. Please try again later','error')
            return redirect(url_for('vehicle.addCustomVehicle'))

        if not VehicleNumber:
            print('VehicleNumber not found')
            flash('An error occured. Please try again later','error')
            return redirect(url_for('vehicle.addCustomVehicle'))

        print(VehicleID, 'VehicleID on top of cursor.execute')
        cursor.execute('SELECT SNo FROM vehicle WHERE VehicleID=VehicleID')
        db.commit()
        SNo = cursor.fetchone()
        print(SNo)
        S_No = SNo[0]

        try:
            update_query = '''
                    UPDATE vehicle
                    SET VehicleType=%s, VehicleNumber=%s, SNo=%s
                    WHERE VehicleID=%s
                '''
            cursor.execute(update_query, (VehicleType, VehicleNumber, S_No, VehicleID))
            db.commit()
        except mysql.connector.Error as e:
            print(e)
            db.rollback()
            flash('Error adding data', 'error')
            return redirect(url_for('vehicle.addCustomVehicle'))
        return redirect(url_for('bookingslot.add_data', VehicleID=VehicleID))
        Blueprint
    cursor.execute("SELECT VehicleID FROM vehicle WHERE VehicleType = '' and VehicleNumber = '' ")
    availableSlots = cursor.fetchall()
    availableSlots = [slot[0] for slot in availableSlots]
    print(availableSlots)


    ####debugging######

    slots2 = session.get('incrementedSNo')

    print('slots2: ', slots2)
    ######end####
    print('available slots: ', availableSlots)
    print('hello    ')
    if not availableSlots:
        flash('No slots found. Please try after sometime', 'error')
        return redirect(url_for('auth.dashboard'))

    return render_template('add/CustomVehicle.html', availableSlots=availableSlots)

@Vehicle.route('/vehicle/anotherSlot/add', methods = ['GET','POST'])
@login_required
def anotherSlot():
    print('inside anotherslot function')
    if request.method == 'POST':
        print('inside the post method')
        VehicleID = request.form['VehicleID']
        
        if not VehicleID:
            flash('Cannot continue without VehicleID. Please try Again later','error')
            return redirect(url_for('vehicle.anotherSlot'))

        session['VehicleID'] = VehicleID
        VehicleType = request.form['VehicleType']
        VehicleNumber = request.form['VehicleNumber']
        username = session.get('username')
        print(username, 'username')
        fetch_query = 'SELECT SNo FROM user WHERE username=%s'
        cursor.execute(fetch_query,(username,))
        db.commit()
        S_No = cursor.fetchone()
        SNo = S_No[0]
        print(SNo, 'SNo')
        if not SNo:
            flash('An error occured','error')
            print('SNo nahi mil raha bhai')
            return redirect(url_for('vehicle.anotherSlot'))

        if not S_No:
            flash('An error occured','error')
            print('S_No nahi mil raha')
            return redirect(url_for('vehicle.anotherslot'))

        if VehicleType == '0':
            flash('Please select a valid Vehicle Type.', 'error')
            return redirect(url_for('vehicle.anotherSlot'))
        if not ValidNumber:
            flash('Registration Number is not valid', 'error')
            return redirect(url_for('vehicle.anotherSlot'))
        try:
            update_query = '''
                    UPDATE vehicle
                    SET VehicleType=%s, VehicleNumber=%s, SNo = %s
                    WHERE VehicleID=%s
                '''
            cursor.execute(update_query, (VehicleType, VehicleNumber, SNo, VehicleID,))
            db.commit()
        except mysql.connector.Error as e:
            db.rollback()
            flash('Error adding new vehicle','error')
            return redirect(url_for('vehicle.anotherSlot'))
        return redirect(url_for('bookingslot.add_data'))

    cursor.execute("SELECT VehicleID, SNo FROM vehicle WHERE VehicleType = '' and VehicleNumber = '' ")

    db.commit()
    availableSlots = cursor.fetchone()
    print(availableSlots)
    VID = availableSlots[0]



    if not availableSlots:
        flash('No slots found. Please try after sometime', 'error')
        return redirect(url_for('app.index'))

    return render_template('add/anotherSlot.html', VID=VID)


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
            return redirect(url_for('bookingslot.add_data'))

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
        if VehicleType in ['sedan', 'Hatchback', 'SUV']:
            print('sedan, hatchback, suv ke andar')
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

        TimeFormat = '%H:%M'
        timeFrom_dt = datetime.strptime(TimeFrom, TimeFormat)
        timeTo_dt = timeFrom_dt + timedelta(hours=durationStr)
        TimeTo = timeTo_dt.strftime(TimeFormat)

        try:
            update_query = '''
            UPDATE vehicle v 
            INNER JOIN bookingslot b ON v.VehicleID = b.BSlotID
            INNER JOIN payment p ON v.VehicleID = p.PaymentID
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

    return render_template('add/adminVehicleSlot.html', VID=VID)


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
