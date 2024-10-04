from flask import redirect, render_template, url_for, request, session, flash, Blueprint
from flask import current_app, g
import mysql.connector
from db import db, cursor
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import re
from utils import requires_role

auth = Blueprint('auth', __name__)

#renders the register form
@auth.route('/register')
def register_form():
    return render_template('auth/register.html')

#regex for valid username
def ValidUser(username):
    pattern = "^[A-z|0-9]"
    return re.match(pattern, username)

#regex for valid contact
def ValidContact(contact):
    pattern = "^(\+91[\-\s]?)?[0]?(91)?[789]\d{9}$"
    return re.match(pattern, contact)

#regex for valid password
def ValidPassword(password):
    pattern = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$"
    return re.match(pattern, password)

#regex for valid name
def ValidName(name):
    pattern = "^[A-z]"
    return re.match(pattern, name)

#regex for valid address
def ValidAddress(address):
    pattern = "[0-9|A-z]"
    return re.match(pattern, address)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST ':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        address = request.form['address']
        contact = request.form['contact']
        S_No = request.form['SNo']
        # session['SNo'] = S_No

        if len(password) > 15:
            flash('Password is too long', 'error')
            return redirect(url_for('auth.register_form'))

        elif len(password) < 6:
            flash('Password should include minimum eight characters, at least one uppercase letter, one lowercase letter, one number and one special character', 'error')
            return redirect(url_for('auth.register_form'))

        if ' ' in username:
            flash('Username cannot contain spaces', 'error')
            return redirect(url_for('auth.register_form'))

        if not ValidUser(username):
            flash('Username cannot contain special characters','error')
            return redirect(url_for('auth.register_form'))

        if not ValidContact(contact):
            flash('Contact is not valid','error')
            return redirect(url_for('auth.register_form'))

        if not ValidPassword(password):
            flash("Password should include minimum eight characters, at least one uppercase letter, one lowercase letter, one number and one special character", "error")
            return redirect(url_for('auth.register_form'))

        if not ValidName(name):
            flash("Name should not contain special characters.", 'error')
            return redirect(url_for('auth.register_form'))

        if not ValidAddress(address):
            flash("Address should not contain special characters","error")
            return redirect(url_for('auth.register_form'))

        #checks if user is already logged in
        check_user_query = 'SELECT username FROM user WHERE username=%s'
        cursor.execute(check_user_query,(username,))
        db.commit()
        existing_user = cursor.fetchone()
        if existing_user:
            flash('Username is already taken. Please try a different username', 'error')
            return redirect(url_for('auth.register_form'))

        try:
            maxSNo = 'SELECT MAX(SNo) FROM user'
            cursor.execute(maxSNo)
            db.commit()
            result = cursor.fetchone()
            maxS_No = result[0]
            incrementedSNo = maxS_No + 1
            session['incrementedSNo'] = incrementedSNo
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            insert_query = '''
                INSERT INTO user(username, password, role, SNo) VALUES (%s, %s, 'user', %s)
            '''
            user_data = (username, hashed_password, incrementedSNo)
            cursor.execute(insert_query, user_data)
            db.commit()
        except mysql.connector.Error as e:
            db.rollback()
            print('Error: ', e)
            flash('Error inserting user','error')
            return redirect(url_for('auth.register_form'))

        try:
            incrementedSNo = session.get('incrementedSNo')
            # print('update wale try mai')
            update_query = '''
                INSERT INTO owner (name, address, contact, SNo) 
                VALUES(%s, %s, %s, %s)
            '''
            cursor.execute(update_query, (name, address, contact, incrementedSNo))
            db.commit()

            return redirect(url_for('auth.dashboard'))

        except mysql.connector.Error as e:
            print(e)
            db.rollback()
            flash('Error adding owner data','danger')
    return render_template('auth/register.html')



##############################Admin login#############################################
@auth.route('/adminlogin')
def AdminLoginForm():
    return render_template('auth/adminlogin.html')

@auth.route('/adminlogin', methods=['POST', 'GET'])
def AdminLogin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = 'admin'

        get_user_query = "SELECT username, password, role, SNo FROM Admin WHERE username=%s"
        cursor.execute(get_user_query, (username,))
        db.commit()
        userData = cursor.fetchone()

        if len(password) > 8:
            flash('Password should not be more than 8 letters', 'error')

        if userData and password: 
            session['username'] = userData[0]
            session['role'] = userData[2]
            return redirect(url_for('auth.admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    print('in get method')
    username = session.get('username')
    #will do after making allotment table functional
    # cursor.execute('SELECT SNo FROM allotment where username=%s')
    db.commit()
    S_No = cursor.fetchone()
    return render_template('auth/adminlogin.html')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if len(password) > 25:
            flash('Password should not be more than 8 characters', 'error')
            return redirect(url_for('auth.login'))

        fetch_query = "SELECT username, password, SNo FROM user WHERE username=%s"
        cursor.execute(fetch_query, (username,))
        user_data = cursor.fetchone()
        db.commit()


        if user_data and check_password_hash(user_data[1], password):
            print('inside the if statement')
            session['username'] = user_data[0]
            session['role'] = 'user'

            if session['role'] == 'admin':
                return redirect(url_for('auth.dashboard'))
            else:
                fetch_query = '''
                    SELECT p.mode FROM Payment p
                    INNER JOIN user u ON p.SNo = u.SNo 
                    WHERE u.username = %s and p.mode <> ''
                '''
                cursor.execute(fetch_query, (username,))
                db.commit()
                data = cursor.fetchone()
                if data is not None:
                    # return redirect(url_for('payment.Generate_Receipt',PaymentID=data[0], SNo=user_data[2]))  
                    return  redirect(url_for('index'))
                else:
                    # return redirect(url_for('vehicle.ChooseVehicle', SNo=user_data[2]))
                    return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')


@auth.route('/login')
def login_form():
    return render_template('auth/login.html')  
    # return render_template('auth/login.html')

@auth.route('/logout')
def logout():
    session.clear()
    if session:
        print(session)
    else:
        print('Logged out successfully')
        print('Session not found')
    return render_template('index.html')


#this ensures that there is no access to website without login
def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        # if session.get('username'):
        if 'username' in session:
            return view(*args, **kwargs)
        else:
            flash('You are not logged in, Please login to continue', 'error')
            return redirect(url_for('auth.login_form'))

        g.user = session['username']
        return view(*args, **kwargs)

    return wrapped_view


cursor.execute('SELECT COUNT(*) FROM slots')
slots_count = cursor.fetchone()

cursor.execute('SELECT COUNT(*) FROM sensor')
sensor_count = cursor.fetchone()

cursor.execute("SELECT COUNT(*) FROM vehicle WHERE VehicleType <> ''")
vehicle_count = cursor.fetchone()

cursor.execute("SELECT COUNT(*) FROM bookingslot WHERE duration <> '' ")
bookingslot_count = cursor.fetchone()

cursor.execute('SELECT COUNT(*) FROM owner')
owner_count = cursor.fetchone()

cursor.execute("SELECT COUNT(*) FROM payment WHERE TotalPrice <> 0")
payment_count = cursor.fetchone()

cursor.execute('SELECT COUNT(*) FROM allotment')
history_count = cursor.fetchone()


@auth.route('/admin')
@requires_role('admin')
def admin_dashboard():
    if 'role' in session:
        return render_template('dashboard.html',
                               slots_count = slots_count[0],
                               vehicle_count = vehicle_count[0],
                               bookingslot_count = bookingslot_count[0],
                               sensor_count = sensor_count[0],
                               owner_count = owner_count[0],
                               history_count = history_count[0],
                               payment_count = payment_count[0], role=session['role'])

    else:
        return redirect(url_for('auth.login_form'))

@auth.route('/user/Bookings')
@login_required
def MyBookingsUser():
    if request.method == 'GET':
        username = session.get('username')
        
        if not username:
            flash('An error ocurred. Please try again later', 'error')
            return redirect(url_for('index'))

        cursor.execute('SELECT SNo FROM user WHERE username=%s', (username,))
        db.commit()
        S_No = cursor.fetchone()
        print('SNo:',S_No)
        if not S_No:
            flash('An error ocurred. Please try again later', 'error')
            # return redirect(url_for('index'))
        SNo = S_No[0]
        if not SNo:
            flash('An error ocurred. Please try again later', 'error')
            # return redirect(url_for('index'))


        try:
            fetch_query = '''
                SELECT * from allotment WHERE username=%s AND TimeTo<curtime()
            '''
            cursor.execute(fetch_query,(username,))
            db.commit()
            data = cursor.fetchall()
            data_list = [[dashboard[0], dashboard[1], dashboard[2], dashboard[3], dashboard[4], dashboard[5], dashboard[6], dashboard[7], dashboard[8], dashboard[9], dashboard[10], dashboard[11], dashboard[12], dashboard[13]] for dashboard in data]
            if not data_list:
                flash('No past bookings', 'success')
        except mysql.connector.Error as e:
            db.rollback()
            flash('An error occurred. Please try again later', 'error')
            return redirect(url_for('index'))
        try:
            fetch_current = '''
                SELECT 
                        o.name, 
                        o.contact, 
                        v.VehicleType, 
                        v.VehicleNumber,
                        b.Date, 
                        b.TimeFrom, 
                        b.TimeTo, 
                        b.duration, 
                        o.address,
                        b.BSlotID AS slot
                    FROM owner o 
                    INNER JOIN vehicle v ON o.SNo = v.SNo
                    INNER JOIN bookingslot b ON o.SNo = b.SNo
                    INNER JOIN user u ON o.SNo = u.SNo
                    WHERE 
                        u.SNo = %s AND (b.Date > CURDATE() OR (b.Date = CURDATE() AND b.TimeTo > CURTIME()))ORDER BY DATE DESC;
            '''
            cursor.execute(fetch_current,(SNo,))
            data = cursor.fetchall()
            datalist = [[booking[0], booking[1], booking[2], booking[3], booking[4], booking[5], booking[6], booking[7], booking[8], booking[9]] for booking in data]

            if not datalist:
                flash('No future bookings', 'success')
        except mysql.connector.Error as e:
            db.rollback()
            flash('An error occured.Please try again later','error')
        

    if 'role' in session:
        return render_template('dashboard.html', data=data_list, datalist = datalist,
                                                 role = session['role'])

@auth.route('/user/dashboard')
@login_required
@requires_role('user')
def dashboard():
    username = session.get('username')
    if request.method == 'GET':
        try:
            fetch_query = '''
                 SELECT u.username, o.name, o.contact, o.address  
                 from user u  
                 inner join owner o on o.SNo = u.SNo  
                 where username=%s
            '''
            cursor.execute(fetch_query,(username,))
            db.commit()
            data = cursor.fetchone()
            print(data)
            username = data[0]
            name = data[1]
            contact = data[2]
            address = data[3]
            print(data)
            if data is None:
                flash('Error fetching your data','error')
                return redirect(url_for('index'))
        except mysql.connector.Error as e:
            db.rollback()
            flash('An error occured. Please try after sometime','error')
            return redirect(url_for('index'))

        try:
            cursor.execute('SELECT SNo FROM user WHERE username=%s', (username,))
            db.commit()
            SNo = cursor.fetchone()[0]
            if SNo is None:
                flash('An error occured. Please try again later', 'error')
                return redirect(url_for('index'))
        except mysql.connector.Error as e:
            db.rollback()
            flash('Server failed')
            return redirect(url_for('auth.dashboard'))

        try:
            fetch_query = 'SELECT * FROM vehicle v INNER JOIN user u on u.SNo=v.SNo WHERE u.SNo=%s AND u.username=%s'
            cursor.execute(fetch_query, (SNo, username,))
            db.commit()
            vehicles = cursor.fetchall()
            vehicleList = [[vehicle[0], vehicle[1], vehicle[2], vehicle[3], vehicle[4]] for vehicle in vehicles]

        except mysql.connector.Error as e:
            db.rollback()
            flash('Server returned a null response. Please try again later','error')
            return redirect(url_for('index'))
    return render_template('userDashboard.html',username=username, name=name, contact=contact, address=address, vehicles=vehicleList)










