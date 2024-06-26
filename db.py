import mysql.connector
db_config1 = {
        'host' : 'localhost',
        'user' : 'root',
        'password' : 'root',
        'database' : 'parking'
        }
db = mysql.connector.connect(**db_config1)
cursor = db.cursor(buffered=True)




