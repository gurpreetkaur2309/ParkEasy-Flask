from flask import session, redirect, render_template, request, flash, Blueprint, url_for
from db import db, cursor
import mysql.connector
from auth import login_required
from utils import requires_role
slots = Blueprint('Slots', __name__)

@slots.route('/slots')
@login_required
@requires_role('admin')
def display():
    cursor.execute('SELECT * FROM slots')
    db.commit()
    data = cursor.fetchall()
    return render_template('view/slots.html', data=data)

@slots.route('/slots/add', methods = ['GET','POST'])
@login_required
def add_data():
    if request.method == 'POST':
        #SlotID = request.form['SlotID']
        space = request.form['space']
        price = request.form['price']
        cursor.execute('INSERT INTO slots(space, price) VALUES(%s, %s)', (space, price))
        db.commit()
        #flash('Data added successfully')
        return redirect(url_for('sensor.add_data'))
    return render_template('add/slots.html')

@slots.route('/slots/edit/<int:SlotID>', methods=['GET','POST'])
@login_required
def edit_data(SlotID):
#    print(SlotID)
    if request.method == 'POST':
        space = request.form['space']
        price = request.form['price']
 #       print(' space and price is ', price, space)
        try:
  #          print('try me gaya')
            update_query = '''UPDATE slots
            SET space =%s, price=%s
            WHERE SlotID=%s'''
            cursor.execute(update_query, (space, price, SlotID))

            db.commit()
            #flash('Data edited successfully')
            return redirect(url_for('Slots.display'))
        except mysql.connector.Error as e:
            db.rollback()
            #flash('Error updating data')
    fetch_query = "SELECT SlotID, space, price FROM slots WHERE SlotID=%s"
    cursor.execute(fetch_query, (SlotID,))
    data = cursor.fetchone()
    print(data)
   # print('this is the one after fetch', data)
    if data is None:
        flash('No data found')
        return redirect(url_for('Slots.display'))
    return render_template('edit/slots.html', data=data)

@slots.route('/slots/delete/<int:SlotID>', methods=['GET','POST'])
@login_required
def delete_data(SlotID):
    if request.method == 'POST':
        # print("in post meth")
        try:
            # print("in try meth")
            delete_query = "DELETE FROM slots WHERE SlotID=%s"
            # print(delete_query)
            cursor.execute(delete_query, (SlotID,))
            print('done')
            #flash('Data deleted  successfully')
            return redirect(url_for('Slots.display'))
        except mysql.connector.Error as e:
            db.rollback()
            #flash('Error deleting data')

    # print("outside of if")
    fetch_query = 'SELECT SlotID, space, price FROM slots WHERE SlotID=%s'
    cursor.execute(fetch_query, (SlotID,))
    db.commit()
    data = cursor.fetchone()
    print(data)
    if data is None:
        flash('No data found')
        return redirect(url_for('Slots.display'))
    return render_template('delete/slots.html', data=data)


