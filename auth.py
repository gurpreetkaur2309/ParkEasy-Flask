from flask import redirect, render_template, url_for, request, session, flash, Blueprint
from flask import current_app, g
import mysql.connector
from db import db, cursor
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import re
from utils import requires_role

auth = Blueprint('auth', __name__)
@auth.route('/register')
def register_form():
    return render_template('auth/register.html')

def ValidUser(username):
    # pattern = "^[a-zA-Z][a-zA-Z\s'-]*$"
    pattern = "^[a-zA-Z0-9_.-]+$"
    return re.match(pattern, username)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    print('register function initiated')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        address = request.form['address']
        contact = request.form['contact']
        S_No = request.form['SNo']
        # session['SNo'] = S_No
        print(session)

        if len(password) > 8:
            flash('Password should not be more than 8 letters', 'error')
            return redirect(url_for('auth.register_form'))

        elif len(password) < 6:
            flash('Password cannot be less than 6 letters', 'error')
            return redirect(url_for('auth.register_form'))

        if ' ' in username:
            flash('Username cannot contain spaces', 'error')
            return redirect(url_for('auth.register_form'))

        if not ValidUser(username):
            flash('Username cannot start with numbers')
            return redirect(url_for('auth.register_form'))

        #Check if username already exists
        check_user_query = 'SELECT username FROM user WHERE username=%s'
        cursor.execute(check_user_query,(username,))
        db.commit()
        existing_user = cursor.fetchone()
        if existing_user:
            flash('Username is already taken. Please try a different username', 'error')
            return redirect(url_for('auth.register_form'))


        print('insert_query executed')
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
            print('insert query wale try mai gaya')
        except mysql.connector.Error as e:
            print('insert query wale except mai gaya')
            db.rollback()
            print('Error: ', e)
            flash('Error inserting user','error')
            return redirect(url_for('auth.register_form'))

        try:
            incrementedSNo = session.get('incrementedSNo')
            print('incrementedSNo: ', incrementedSNo)
            # print('update wale try mai')
            update_query = '''
                INSERT INTO owner (name, address, contact, SNo) 
                VALUES(%s, %s, %s, %s)
            '''
            print('update query ke niche cursor.execute ke upar')
            cursor.execute(update_query, (name, address, contact, incrementedSNo))
            print('db.commit ke upar')
            db.commit()
            print('mydata', name, address, contact, incrementedSNo)
            print('Owner data added successfully')
            return redirect(url_for('auth.dashboard'))
        except mysql.connector.Error as e:
            print('Update wale except mai')
            print(e)
            db.rollback()
            flash('Error adding owner data','danger')
    print('in get method of refgister')
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
        print(userData[0])
        print('user data: ', userData)

        if len(password) > 8:
            flash('Password should not be more than 8 letters', 'error')

        if userData and password: 
            session['username'] = userData[0]
            session['role'] = userData[2]
            print(session['role'])
            return redirect(url_for('auth.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    print('in get method')
    username = session.get('username')
    cursor.execute('SELECT SNo FROM allotment where username=%s')
    db.commit()
    S_No = cursor.fetchone()
    print('S_No: ', S_No)
    return render_template('auth/adminlogin.html')





# @auth.route('/login', methods=['GET','POST'])
# def login():
#     print('On top of request.form')
#     if request.method == 'POST':
#         print('inside post method')
#         username = request.form['username']
#         session['username'] = username
#         password = request.form['password']
#         if len(password) > 8:
#             flash('Password should not be more than 8 letters', 'error')

#         get_user_query = "SELECT username, password, SNo FROM user WHERE username=%s"
#         cursor.execute(get_user_query,(username,))
#         db.commit()
#         user_data = cursor.fetchone()
#         print(user_data)
#         if user_data and check_password_hash(user_data[1], password):
#             print('inside the if statement')
#             session['username'] = user_data[0]
#             session['role'] = 'user'

#             if session['role'] == 'admin':
#                 return redirect(url_for('auth.dashboard'))
#             else:
#                 return redirect(url_for('vehicle.add_data'))
#         else:
#             print('inside the else condition')
#             flash('Invalid username or password', 'error')
#             return redirect(url_for('auth.login_form'))

#     print('bottom of the post') 
#     # username = session.get('username')
#     # print(username, 'username')
#     # select_query = '''
#     #      SELECT SNo FROM user where username=%s
#     #  '''
#     # cursor.execute(select_query,(username,))
#     # db.commit()
    
    
#     # SID = session.get('SNo')
#     # print(SNo)
#     # print('hello world')
#     return render_template('auth/login.html')



@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        print('inside post method')
        username = request.form['username']
        password = request.form['password']

        if len(password) > 8:
            flash('Password should not be more than 8 characters', 'error')
            return redirect(url_for('auth.login'))

        get_user_query = "SELECT username, password, SNo FROM user WHERE username=%s"
        cursor.execute(get_user_query, (username,))
        user_data = cursor.fetchone()
        db.commit()
        print(user_data)

        if user_data and check_password_hash(user_data[1], password):
            print('inside the if statement')
            session['username'] = user_data[0]
            session['role'] = 'user'

            if session['role'] == 'admin':
                return redirect(url_for('auth.dashboard'))
            else:
                return redirect(url_for('vehicle.add_data'))
        else:
            print('inside the else condition')
            flash('Invalid username or password', 'error')
            return redirect(url_for('auth.login'))

    # Handling GET request
    print('inside get method')
    username = session.get('username')
    print(username, 'username')

    if username:
        select_query = '''
            SELECT SNo FROM user WHERE username=%s
        '''
        cursor.execute(select_query, (username,))
        user_data = cursor.fetchone()
        db.commit()
        SID = user_data[0] if user_data else None
    else:
        SID = None

    print(SID)
    print('hello world')
    return render_template('auth/login.html', SID=SID)





@auth.route('/login')
def login_form():
    username = session.get('username')
    print(username, 'username')
    if username:
        select_query = '''
            SELECT SNo FROM user WHERE username=%s
        '''
        cursor.execute(select_query, (username,))
        db.commit()
        user_data = cursor.fetchone()
        SID = user_data[0] if user_data else None
        print(SID)
    else:
        print('Your SID is None')
    
    # print(SID)
    print('hello world')
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


# Login required for authentication
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

cursor.execute('SELECT COUNT(*) FROM vehicle')
vehicle_count = cursor.fetchone()

cursor.execute('SELECT COUNT(*) FROM bookingslot')
bookingslot_count = cursor.fetchone()

cursor.execute('SELECT COUNT(*) FROM owner')
owner_count = cursor.fetchone()

cursor.execute('SELECT COUNT(*) FROM payment')
payment_count = cursor.fetchone()



####dashboard########
@auth.route('/dashboard')
def dashboard():
    if 'role' in session:
        return render_template('dashboard.html',
                               slots_count = slots_count[0],
                               vehicle_count = vehicle_count[0],
                               bookingslot_count = bookingslot_count[0],
                               sensor_count = sensor_count[0],
                               owner_count = owner_count[0],
                               payment_count = payment_count[0], role=session['role'])

    else:
        return redirect(url_for('auth.login_form'))


@auth.route('/user/dashboard')
def UserDashboard():
    print('Get request ke upar')
    if request.method == 'GET':
        print('fetch query ke upar')
        fetch_query = '''
            SELECT o.name, o.contact, 
            v.VehicleType, v.VehicleNumber,
            b.Date, b.TimeFrom, b.TimeTo, b.duration,o.address,
            b.BSlotID as slot
            FROM owner o 
            INNER JOIN vehicle v ON o.OwnerID = v.VehicleID
            INNER JOIN bookingslot b on o.OwnerID = b.BSlotID
            -- WHERE o.OwnerID=%s;

        '''

        cursor.execute(fetch_query)
        db.commit()
        data = cursor.fetchone()

        OwnerName = data[0]
        print(OwnerName)
        OwnerContact = data[1]
        VehicleType = data[2]
        VehicleNumber = data[3]
        Date = data[4]
        TimeFrom = data[5]
        TimeTo = data[6]
        duration = data[7]
        address = data[8]
        Slot = data[9]

        print(OwnerName, OwnerContact, VehicleType, VehicleNumber, Date, TimeFrom, TimeTo, duration, address, Slot)
    if 'role' in session:
        return render_template('dashboard.html', OwnerName = data[0], OwnerContact=data[1], VehicleType=data[2], VehicleNumber=data[3], Date=data[4], TimeFrom=data[5], TimeTo=data[6], duration=data[7], address=data[8], Slot=data[9], role = session['role'])

