from flask import redirect, render_template, request, url_for, session, Blueprint, flash
import mysql.connector
from db import db, cursor
from auth import login_required
from utils import  requires_role
sensor = Blueprint('sensor', __name__)


@sensor.route('/sensor')
@requires_role('admin')
def display():
    update_query = '''
        UPDATE sensor s
        JOIN bookingslot b ON s.SensorID = b.BSlotID
        SET isParked == 0
        WHERE b.TimeFrom is Null AND b.TimeTo is Null
    '''
    try:
        cursor.execute(update_query)
        db.commit()
    except mysql.connector.Error as e:
        db.rollback()
        flash("Error updating data to null")
    cursor.execute('SELECT * FROM sensor')
    db.commit()
    data = cursor.fetchall()
    Null_query = '''
        SELECT s.SensorID, s.isParked
        FROM sensor s
        JOIN bookingslot b ON s.SensorID = b.BSlotID
        WHERE b.TimeFrom is Null and b.TimeTo is Null
        
    '''
    cursor.execute(Null_query)
    NullID=cursor.fetchall()
    return render_template('view/sensor.html',data=data,NullID=NullID)


@sensor.route('/sensor/add', methods=['GET','POST'])
@login_required
def add_data():
    if request.method == 'POST':
        #SensorID = request.form['SensorID']
        isParked = request.form['isParked']
        cursor.execute('INSERT INTO sensor(isParked) VALUES(%s)', (isParked,))
        db.commit()
        #flash('Data added successfully')
        return redirect(url_for('sensor.display'))
    return render_template('add/sensor.html')

@sensor.route('/sensor/edit/<int:SensorID>', methods=['GET','POST'])
@login_required
def edit_data(SensorID):
    if request.method == 'POST':
        isParked = request.form['isParked']
        try:
            update_query = '''UPDATE sensor
            SET isParked=%s
            WHERE SensorID=%s'''
            cursor.execute(update_query, (isParked, SensorID,))
            db.commit()
            #flash('Data updated successfully')
            return redirect(url_for('sensor.display'))
        except mysql.connector.Error as e:
            db.rollback()
            #flash('Error updating data')
    fetch_query = 'SELECT SensorID, isParked FROM sensor WHERE SensorID=%s'
    cursor.execute(fetch_query, (SensorID,))
    db.commit()
    data = cursor.fetchone()
    if data is None:
        flash('Data not found')
        return redirect(url_for('sensor.display'))
    return render_template('edit/sensor.html', data=data)

@sensor.route('/sensor/delete/<int:SensorID>', methods=['GET','POST'])
@login_required
def delete_data(SensorID):
    if request.method == 'POST':
        try:
            delete_query = 'DELETE FROM sensor WHERE SensorID=%s'
            cursor.execute(delete_query, (SensorID,))
            db.commit()
            #flash('Data deleted successfully')
            return redirect(url_for('sensor.display'))
        except mysql.connector.Error as e:
            db.rollback()
            #flash('Error deleting data')
    fetch_query = 'SELECT SensorID, isParked FROM sensor WHERE SensorID=%s'
    cursor.execute(fetch_query, (SensorID,))
    db.commit()
    data = cursor.fetchone()
    if data is None:
        flash('Data not found')
        return redirect(url_for('sensor.display'))
    return render_template('delete/sensor.html', data=data)























