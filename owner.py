from flask import redirect, render_template, session, request, Blueprint, url_for, flash
import mysql.connector
from db import db, cursor
from auth import login_required
import re
owner = Blueprint('owner', __name__)

@owner.route('/owner')
@login_required
def display():
    update_query = '''
        UPDATE owner o
        JOIN bookingslot b on o.OwnerID = b.BSlotID
        SET o.Name=Null, o.contact = Null, o.address = Null
        WHERE b.TimeFrom is Null and b.TimeTo is Null
    '''
    try:
        cursor.execute(update_query)
        db.commit()
    except mysql.connector.Error as e:
        db.rollback()
        flash('Error updating data to null')

    cursor.execute('SELECT * FROM owner')
    db.commit()
    data = cursor.fetchall()

    Null_query = '''
        SELECT o.OwnerID
        FROM Owner o
        JOIN bookingslot b on o.OwnerID = b.BSlotID
        WHERE b.TimeFrom is Null and b.TimeTo is Null
    '''
    cursor.execute(Null_query)
    NullID = cursor.fetchall()
    return render_template('view/owner.html', data=data, NullID=NullID)

def ValidContact(contact):
    pattern = r"^[6-9]\d*$"
    return re.match(pattern, contact)
def ValidName(Name):
    pattern = r"^[a-zA-Z][a-zA-Z\s'-]*$"
    return re.match(pattern, Name)

@owner.route('/owner/add', methods = ['GET','POST'])
@login_required
def add_data():
    # SharedID = session.get('SharedID')
    if request.method == 'POST':
        print("In try")
        OwnerID = session.get('VehicleID')
        print("OwnerID: ", OwnerID)
        Name = request.form['Name']
        contact = request.form['contact']
        address = request.form['address']
        print(request.form)

        if not ValidName(Name):
            flash('Name should start with an alphabet','error')
            return redirect(url_for('owner.add_data'))

        if not ValidContact(contact):
            print("not valid")
            flash('Mobile number not valid', 'error')
            return redirect(url_for('owner.add_data'))
        
        if len(contact) > 12:
            flash('Contact connot be more than 12 numbers')
            return redirect(url_for('owner.add_data'))
        
        update_query = '''
            UPDATE owner
            SET Name=%s, contact=%s, address=%s
            WHERE OwnerID=%s
        '''
        cursor.execute(update_query, (Name, contact, address, OwnerID))
        db.commit()
        #flash('Data added successfully')
        # return redirect(url_for('payment.add_data'))
        return redirect(url_for('payment.add_data', VehicleID=OwnerID))
    cursor.execute('SELECT OwnerID FROM owner WHERE Name is Null and contact is Null and address is Null')
    availableSlots = cursor.fetchone()
    return render_template('add/owner.html', availableSlots=availableSlots)

@owner.route('/payment/add/<int:VehicleID>')
@login_required
def Payment(OwnerID):
    return render_template('add/payment.html', VehicleID=OwnerID)

@owner.route('/owner/edit/<int:OwnerID>', methods=['GET','POST'])
@login_required
def edit_data(OwnerID):
    if request.method == 'POST':
        Name = request.form['Name']
        contact = request.form['contact']
        address = request.form['address']
        try:
           update_query = '''UPDATE owner
           SET Name=%s, contact=%s, address=%s
           WHERE OwnerID=%s'''
           cursor.execute(update_query, (Name, contact, address, OwnerID,))
           db.commit()
           #flash('Data updated successfully')
           return redirect(url_for('owner.display'))
        except mysql.connector.Error as e:
            db.rollback()
            #flash('Error updating data')
    fetch_query = 'SELECT OwnerID, name, contact, address FROM owner WHERE OwnerID=%s'
    cursor.execute(fetch_query, (OwnerID,))
    db.commit()
    data = cursor.fetchone()
    if data is None:
        flash('No data found')
        return redirect(url_for('owner.display'))
    return render_template('edit/owner.html',data=data)

@owner.route('/owner/delete/<int:OwnerID>', methods = ['GET', 'POST'])
@login_required
def delete_data(OwnerID):
    if request.method == 'POST':
        try:
            delete_query = '''DELETE FROM owner WHERE OwnerID=%s'''
            cursor.execute(delete_query, (OwnerID,))
            db.commit()
            #flash('Data deleted successfully')
            return redirect(url_for('owner.display'))
        except mysql.connector.Error as e:
            db.rollback()
            print(e)
            print('In the except')
            flash('Error deleting data')
    fetch_query = 'SELECT OwnerId, name, contact, address FROM owner WHERE OwnerID=%s'
    cursor.execute(fetch_query, (OwnerID,))
    db.commit()
    data = cursor.fetchone()
    if data is None:
        flash('Data not found')
        return redirect(url_for('owner.display'))
    return render_template('delete/owner.html', data=data)




