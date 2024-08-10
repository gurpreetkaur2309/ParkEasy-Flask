import re
from flask import redirect, render_template, session, url_for, Blueprint, flash, request
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
    SNo = request.args.get('SNo')  
    if request.method == 'POST':
        VehicleID = request.form.get('VehicleID')
        if not VehicleID:
            print('vehicle id ni h')
            flash('Cannot continue without vehicleID', 'danger')
            return redirect(url_for('vehicle.add_data', SNo=SNo))  
        session['VehicleID'] = VehicleID
        VehicleType = request.form.get('VehicleType')
        VehicleNumber = request.form.get('VehicleNumber')
        S_No = SNo if SNo else session.get('incrementedSNo')
        
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
            cursor.execute(update_query, (VehicleType, VehicleNumber, S_No, VehicleID))
            db.commit()

            print('db.commit k niche')
        except mysql.connector.Error as e:
            print(e)
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
    username = session.get('username')
    print('username: ', username)
    fetch_query = 'SELECT SNo FROM user WHERE username=%s'
    cursor.execute(fetch_query, (username,))
    db.commit()
    SNo = cursor.fetchone()[0]
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
    print('inside custom vehicle function')
    SNo = session.get('incrementedSNo')
    print(SNo, 'SNo')
    if request.method == 'POST':
        print('inside post method')
        VehicleID = request.form['VehicleID']
        if not VehicleID:
            flash('Cannot continue without vehicleID', 'danger')
            return redirect(url_for('vehicle.add_data'))
        # VehicleID = int(VehicleID)

        session['VehicleID'] = VehicleID
        VehicleType = request.form['VehicleType']
        if VehicleType == '0':
            flash('Please select a valid VehicleType','danger')
            return redirect(url_for('vehicle.addCustomVehicle'))
        VehicleNumber = request.form['VehicleNumber']
        if not ValidNumber(VehicleNumber):
            flash('Registration Number is not valid')
            return redirect(url_for('vehicle.add_data'))
        S_No = session.get('incrementedSNo')
        print('sno: ', S_No)
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
    if request.method == 'POST':
        VehicleID = request.form['VehicleID']
        if not VehicleID:
            flash('Cannot continue without VehicleID. Please try Again later','error')
            return redirect(url_for('vehicle.anotherSlot'))
        session['VehicleID'] = VehicleID
        VehicleType = request.form['VehicleType']
        VehicleNumber = request.form['VehicleNumber']
        cursor.execute('SELECT SNo FROM vehicle WHERE VehicleID=%s')
        db.commit()
        S_No = cursor.fetchone()
        SNo = S_No[0]
        print(SNo, 'SNo')
        print
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
        return redirect(url_for('auth.dashboard'))

    return render_template('add/vehicle.html', VID=VID)




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
