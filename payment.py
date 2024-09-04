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
    update_query = '''
        UPDATE payment p
        JOIN bookingslot b ON p.PaymentID = b.BSlotID
        SET TotalPrice=Null, Mode=Null
        WHERE b.TimeFrom is Null and b.TimeTo is Null
    '''
    try:
        cursor.execute(update_query)
        db.commit()
    except mysql.connector.Error as e:
        db.rollback()
        flash('Error updating data to null')

    cursor.execute('SELECT * FROM payment')
    db.commit()
    data = cursor.fetchall()

    Null_query = 'SELECT p.PaymentID FROM payment p JOIN bookingslot b on p.PaymentID = b.BSlotID WHERE b.TimeFrom is Null and b.TimeTo is Null'
    cursor.execute(Null_query)
    NullID = cursor.fetchone()

    return render_template('view/payment.html', data=data, NullID=NullID)

@payment.route('/payment/add', methods=['GET', 'POST'])
@login_required
def add_data():
    if request.method == 'POST':
        print('request.form ke niche')
        PaymentID = session.get('VehicleID')
        VehicleID = session.get('VehicleID')
        print('PaymentID in post', PaymentID)
        mode = request.form['mode']
        cursor.execute('SELECT SNo FROM vehicle WHERE VehicleID=%s', (VehicleID,))
        db.commit()
        SNo = cursor.fetchone()
        S_No = SNo[0]
        # S_No = session.get('incrementedSNo')
        # print('S_No: ', S_No)
        if not S_No:
            flash('S_No nahi mil raha bhai','error')
            return redirect(url_for('payment.add_data', VehicleID=PaymentID, SNo = S_No))
        #debugging
        data = ('debugging', PaymentID, mode)
        print(data)
        ##end##`
        OwnerID = PaymentID
        BSlotID = PaymentID
        VehicleID = PaymentID

        print('all ids are: ', OwnerID, BSlotID, VehicleID)

        try:
            print('fetch query ke upar in try')
            
            fetch_query = '''
                SELECT      v.VehicleID,      v.VehicleType,      v.VehicleNumber,     b.Date,      b.TimeFrom,      b.TimeTo,      b.duration,     u.SNo,      u.username,     o.name,      o.contact,     p.TotalPrice,      p.mode FROM      vehicle v  JOIN      bookingslot b ON v.VehicleID = b.BSlotID JOIN      user u ON v.SNo = u.SNo JOIN      owner o ON u.SNo = o.SNo JOIN      payment p ON b.BSlotID = p.PaymentID ORDER BY      b.Date DESC, b.TimeFrom DESC LIMIT 1
            '''
            cursor.execute(fetch_query, (PaymentID,))
            data = cursor.fetchone()
            print('data in try is',data)

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
            Duration = int(duration)
            


            print('TimeTo: ', TimeTo,'TimeFrom:', TimeFrom)
            rate = 0
            if VehicleType in ['sedan', 'SUV', 'Hatchback', 'Coupe']:
                rate = 13
            elif VehicleType == '2-Wheeler':
                rate = 8
            elif VehicleType == 'Heavy-Vehicle':
                rate = 15
            elif VehicleType == 'Luxury-Vehicle':
                rate = 18


            print('rate', rate)
            print('duration', duration)
            TotalPrice = rate * Duration 
            print(TotalPrice)
            TotalPrice = float(TotalPrice)
            session['TotalPrice'] = TotalPrice
            print(session, 'totalprice')


            print('Update query ke upar')
            update_query = '''
                UPDATE payment
                SET TotalPrice=%s, mode=%s, SNo=%s
                WHERE PaymentID=%s
            '''

                        
            cursor.execute(update_query, (TotalPrice, mode, S_No, PaymentID,))
            db.commit()

            try:
                insert_query = '''
                    INSERT INTO allotment(VehicleID, SNo, username, date, TimeFrom, TimeTo, duration, name, contact, TotalPrice, mode, VehicleType, VehicleNumber) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)                '''
                # cursor.execute(insert_query, (VehicleID, username, date, TimeFrom, TimeTo, Duration, name, contact, TotalPrice, mode, VehicleType, VehicleNumber))
                cursor.execute(insert_query, (VehicleID, S_No, username, date, TimeFrom, TimeTo, Duration, name, contact, TotalPrice, mode, VehicleType, VehicleNumber))

                db.commit()
            except mysql.connector.Error as e:
                print(e)
                flash('Error adding allotment', 'error')
                return redirect(url_for('payment.add_data'))

            return redirect(url_for('payment.Generate_Receipt',duration=duration, TotalPrice=TotalPrice, PaymentID=PaymentID))
            # return render_template('add/payment.html',duration=duration, TotalPrice=TotalPrice, PaymentID=PaymentID)

        except mysql.connector.Error as e:
            print('post wale except ke andar')
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

    Null_query = '''
        SELECT v.VehicleType, v.VehicleNumber, p.TotalPrice
        FROM vehicle v 
        JOIN bookingslot b ON v.VehicleID = b.BSlotID
        JOIN payment p ON v.VehicleID = p.PaymentID
        WHERE b.TimeFrom is Null AND b.TimeTo is Null
        
    '''
    cursor.execute(Null_query)
    NullID = cursor.fetchall()

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
        elif VehicleType == 'Sedan':
            rate = 13
        elif VehicleType == 'SUV':
            rate = 13
        elif VehicleType == 'Hatchback':
            rate = 13
        elif VehicleType == 'Heavy-Vehicle':
            rate = 15
        elif VehicleType == 'Luxury-Vehicle':
            rate = 18
        Price = rate * duration
        return render_template('view/GenerateReceipt.html', strftime=datetime.strftime, PaymentID=PaymentID,
                               VehicleType=VehicleType, VehicleNumber=VehicleNumber, date=Date, ReceiptID=ReceiptID, Price=Price, Mode=Mode, TimeFrom=TimeFrom, TimeTo=TimeTo, SNo=SNo)

    except mysql.connector.Error as e:
        print(e)
        db.rollback()
        flash('Error generating receipt', 'error')
        return redirect(url_for('payment.display'))



