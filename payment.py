from flask import redirect, render_template, request, url_for, Blueprint, flash, session
from db import db, cursor
import mysql.connector
from auth import login_required
from datetime import datetime, time
from utils import requires_role
import pdb

payment = Blueprint('payment', __name__)

@payment.route('/payment')
@login_required
@requires_role('admin')
def display():

    fetch_query = '''
        SELECT p.PaymentID, if(p.TotalPrice = 0, '', p.TotalPrice) as formatted_Price, p.mode 
        FROM payment p
    '''
    cursor.execute(fetch_query)
    db.commit()
    data = cursor.fetchall()

    Null_query = 'SELECT p.PaymentID FROM payment p JOIN bookingslot b on p.PaymentID = b.BSlotID WHERE b.TimeFrom is Null and b.TimeTo is Null'
    cursor.execute(Null_query)
    NullID = cursor.fetchone()

    return render_template('view/payment.html', data=data, NullID=NullID)

@payment.route('/payment/add', methods=['GET', 'POST'])
@login_required
def add_data():
    print('add_data ke andar')
    if request.method == 'POST':
        print('post method k andar')
        PaymentID = session.get('VehicleID')
        print('paymentID', PaymentID)
        VehicleID = session.get('VehicleID')
        print('VehicleID', VehicleID)
        mode = request.form['mode']
        print('mode', mode)
        cursor.execute('SELECT SNo FROM vehicle WHERE VehicleID=%s', (VehicleID,))
        db.commit()
        SNo = cursor.fetchone()
        print('sno', SNo)
        S_No = SNo[0]
        # S_No = session.get('incrementedSNo')
        # print('S_No: ', S_No)
        if not S_No:
            flash('S_No nahi mil raha bhai','error')
            return redirect(url_for('payment.add_data', VehicleID=PaymentID, SNo = S_No))
        try:
            fetchData = '''
                SELECT v.VehicleType, b.duration FROM vehicle v 
                JOIN bookingslot b ON v.VehicleID = b.BSlotID
                WHERE VehicleID=%s
                '''
            cursor.execute(fetchData, (VehicleID,))
            v_data = cursor.fetchone();
            print(v_data)
            if not v_data:
                flash('v_data not found','error')
                return redirect(url_for('payment.add_data'))
            VehicleType = v_data[0]
            duration = v_data[1]
            Duration = int(duration)
            print(Duration, 'duration')
            print(VehicleType, 'VehicleType')
            rate = 0
            if VehicleType == 'car':
                rate = 13
            elif VehicleType == '2-Wheeler':
                rate = 8
            elif VehicleType == 'Heavy-Vehicle':
                rate = 15
            elif VehicleType == 'Luxury-Vehicle':
                rate = 18

            TotalPrice = rate * Duration 
            TotalPrice = float(TotalPrice)
            session['TotalPrice'] = TotalPrice
            print(TotalPrice, 'TotalPrice')
            print('update query wale try ke andar')
            update_query = '''
                UPDATE payment
                SET TotalPrice=%s, mode=%s, SNo=%s
                WHERE PaymentID=%s
            '''
            cursor.execute(update_query, (TotalPrice, mode, S_No, PaymentID,))
            db.commit()
        except mysql.connector.Error as e:
            print('update query wale except ke andar')

            db.rollback()
            print(e)
            flash('Error adding your data','error')
            return redirect(url_for('payment.add_data', PaymentID=PaymentID, SNo=SNo))
       
        try:
            print('fetch query wale try ke andar')
            fetch_query = '''
                SELECT v.VehicleID, v.VehicleType, v.VehicleNumber, 
                       b.Date, b.TimeFrom, b.TimeTo, b.duration, 
                       u.SNo, u.username,     
                       o.name, o.contact,     
                       p.TotalPrice, p.mode 
                       FROM vehicle v
                       JOIN bookingslot b ON v.VehicleID = b.BSlotID 
                       JOIN user u ON v.SNo = u.SNo 
                       JOIN owner o ON u.SNo = o.SNo 
                       JOIN payment p ON b.BSlotID = p.PaymentID 
                       ORDER BY  b.Date DESC, 
                       b.TimeFrom DESC LIMIT 1
            '''
            cursor.execute(fetch_query)
            data = cursor.fetchone()
            print(data)
            if data is None:
                print('No data')
                flash('No data found', 'error')
                return redirect(url_for('payment.add_data'))

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
            
            
            
            #debugging
            cursor.execute('SELECT TotalPrice, mode, SNo FROM payment WHERE PaymentID=%s',(PaymentID,))
            db.commit()
            data1 = cursor.fetchone()
            #end
                        
            

            try:
                print('insert query wale try ke andar')
                insert_query = '''
                    INSERT INTO allotment(VehicleID, SNo, username, date, TimeFrom, TimeTo, duration, name, contact, TotalPrice, mode, VehicleType, VehicleNumber) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)                '''
                # cursor.execute(insert_query, (VehicleID, username, date, TimeFrom, TimeTo, Duration, name, contact, TotalPrice, mode, VehicleType, VehicleNumber))
                cursor.execute(insert_query, (VehicleID, S_No, username, date, TimeFrom, TimeTo, Duration, name, contact, TotalPrice, mode, VehicleType, VehicleNumber))

                db.commit()
            except mysql.connector.Error as e:
                print('insert query wale allotment ke andar')
                print(e)
                flash('Error adding allotment', 'error')
                return redirect(url_for('payment.add_data'))

            return redirect(url_for('payment.Generate_Receipt',duration=duration, TotalPrice=TotalPrice, mode=mode, PaymentID=PaymentID))
            # return render_template('add/payment.html',duration=duration, TotalPrice=TotalPrice, PaymentID=PaymentID)

        except mysql.connector.Error as e:
            print('fetch query wale except ke andar')
            print(e)
            db.rollback()
            flash('Error processing your payment', 'error')
            return redirect(url_for('payment.add_data'))

    
    Amount = session.get('TotalPrice')
    return render_template('add/payment.html', Amount = Amount)



def receipt(PaymentID):
    return render_template('view/GenerateReceipt.html',PaymentID=PaymentID)


@payment.route('/payment/edit/<int:PaymentID>', methods = ['GET','POST'])
@login_required
def edit_data(PaymentID):
    if request.method == 'POST':
        TotalPrice = request.form['TotalPrice']
        Mode = request.form['Mode']
        try:
            update_query = '''UPDATE payment
            SET TotalPrice=%s, Mode=%s
            WHERE PaymentID=%s'''
            cursor.execute(update_query, (TotalPrice, Mode, PaymentID,))
            #flash('Data updated successfully')
            return redirect(url_for('payment.display'))
        except mysql.connector.Error as e:
            db.rollback()
            flash('Error updating data')
    fetch_query = 'SELECT PaymentID, TotalPrice, Mode FROM payment WHERE PaymentID=%s'
    cursor.execute(fetch_query, (PaymentID,))
    db.commit()
    data = cursor.fetchone()
    if data is None:
        flash('No data found')
        return redirect(url_for('payment.display'))
    return render_template('edit/payment.html', data=data)

@payment.route('/payment/delete/<int:PaymentID>', methods = ['GET','POST'])
@login_required
def delete_data(PaymentID):
    if request.method == 'POST':

        try:
            delete_query = 'DELETE FROM payment WHERE PaymentID = %s'
            cursor.execute(delete_query, (PaymentID,))
            db.commit()
            #flash('Data deleted successfully')
            return redirect(url_for('payment.display'))
        except mysql.connector.Error as e:
            db.rollback()
            flash('Error deleting data')
    fetch_query = 'SELECT PaymentID, TotalPrice, Mode FROM payment WHERE PaymentID = %s'
    cursor.execute(fetch_query, (PaymentID,))
    db.commit()
    data = cursor.fetchone()
    if data is None:
        flash('No data found')
        return redirect(url_for('payment.display'))
    return render_template('delete/payment.html',data=data)

@payment.route('/payment/generate_receipt/<int:PaymentID>', methods=['GET', 'POST'])
@login_required

def Generate_Receipt(PaymentID):

    try:
        fetch_query = '''
            SELECT v.SNo, v.VehicleType, v.VehicleNumber, b.date, p.PaymentID, p.TotalPrice, p.Mode, b.TimeFrom, b.TimeTo
            FROM payment p 
            JOIN bookingslot b ON p.PaymentID = b.BSlotID 
            JOIN vehicle v  ON p.PaymentID = v.VehicleID
            WHERE p.PaymentID=%s
        '''
        cursor.execute(fetch_query, (PaymentID,))
        db.commit()
        data = cursor.fetchone()
        print(data)
        # VehicleType, VehicleNumber, ReceiptID, Price, date, Mode, TimeFrom, TimeTo = data
        if data is None:
            flash('Slot not booked. Please book the slot to generate receipt', 'danger')
            return redirect(url_for('payment.display'))
        if data[5] == 0.0:
            return redirect(url_for('vehicle.add_data',SNo=data[0]))

        SNo = data[0]
        VehicleType = data[1]
        VehicleNumber = data[2]
        Date = data[3]
        ReceiptID = data[4]
        Price = data[5]
        Mode = data[6]
        TimeFrom = data[7]
        TimeTo = data[8]

        if TimeFrom is None or TimeTo is None:
            flash('Booking slot time data is missing', 'error')
            return redirect(url_for('payment.display'))

        duration = (datetime.strptime(str(TimeTo), '%H:%M:%S') - datetime.strptime(str(TimeFrom), '%H:%M:%S')).seconds / 3600

        rate=0
        if VehicleType == '2-Wheeler':
            rate = 8
        elif VehicleType == 'car':
            rate = 13
        elif VehicleType == 'Heavy-Vehicle':
            rate = 15
        elif VehicleType == 'Luxury-Vehicle':
            rate = 18
        Price = rate * duration
        
    except mysql.connector.Error as e:
        print(e)
        db.rollback()
        flash('Error generating receipt', 'error')
        return redirect(url_for('payment.display'))

    try:
        username = session.get('username')
        print(username)
        cursor.execute('SELECT * FROM allotment WHERE username=%s', (username,))
        db.commit()
    except mysql.connector.Error as e:
        print(e)
        db.rollback()
        return redirect(url_for('payment.Generate_Receipt', PaymentID=PaymentID))

    return render_template('view/GenerateReceipt.html', strftime=datetime.strftime, PaymentID=PaymentID,
                               VehicleType=VehicleType, VehicleNumber=VehicleNumber, date=Date, ReceiptID=ReceiptID, Price=Price, Mode=Mode, TimeFrom=TimeFrom, TimeTo=TimeTo, SNo=SNo)




